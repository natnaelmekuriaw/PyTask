import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import Task, TaskStatus
from pytask_service.example_tasks import registry
from pytask_service.policy import TaskPolicy
from pytask_service.tasks import submit_task
from pytask_service.worker.outcome import TaskOutcome
from pytask_service.worker.service import Worker


@pytest.mark.integration
def test_idle_worker_does_not_run_executor(isolated_engine: Engine) -> None:
    def unexpected_executor(path: str, claim: object, cancel: object) -> TaskOutcome:
        raise AssertionError("No task should be executed")

    worker = Worker(
        isolated_engine,
        "pytask_service.example_tasks:registry",
        executor=unexpected_executor,
    )

    assert worker.run_once() is None


@pytest.mark.integration
def test_worker_claims_executes_and_finishes_task(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        task_id = submit_task(session, registry, "math.add", {"left": 2, "right": 3})

    worker = Worker(
        isolated_engine,
        "pytask_service.example_tasks:registry",
        worker_id="worker-one",
        executor=lambda path, claim, cancel: TaskOutcome.success(5),
    )
    worked = worker.run_once()

    assert worked is not None
    assert worked.id == task_id
    assert worked.outcome.result == 5
    with Session(isolated_engine) as session:
        task = session.get(Task, task_id)
        assert task is not None
        assert task.status == TaskStatus.SUCCEEDED.value
        assert task.result == 5


@pytest.mark.integration
def test_worker_runs_real_child_process(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        task_id = submit_task(session, registry, "math.add", {"left": 7, "right": 8})

    worker = Worker(isolated_engine, "pytask_service.example_tasks:registry")
    worked = worker.run_once()

    assert worked is not None
    assert worked.outcome.succeeded
    with Session(isolated_engine) as session:
        task = session.get(Task, task_id)
        assert task is not None
        assert task.status == TaskStatus.SUCCEEDED.value
        assert task.result == 15


@pytest.mark.integration
def test_worker_records_handler_failure(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        task_id = submit_task(
            session, registry, "demo.fail", {"message": "expected failure"}, policy=TaskPolicy(max_attempts=1)
        )

    worker = Worker(
        isolated_engine,
        "pytask_service.example_tasks:registry",
        executor=lambda path, claim, cancel: TaskOutcome.failure(RuntimeError("failed")),
    )
    worked = worker.run_once()

    assert worked is not None
    assert not worked.outcome.succeeded
    with Session(isolated_engine) as session:
        task = session.get(Task, task_id)
        assert task is not None
        assert task.status == TaskStatus.FAILED.value
        assert task.error is not None


@pytest.mark.integration
def test_worker_records_executor_error(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        task_id = submit_task(session, registry, "math.add", {"left": 1, "right": 2}, policy=TaskPolicy(max_attempts=1))

    def broken_executor(path: str, claim: object, cancel: object) -> TaskOutcome:
        raise OSError("process launch failed")

    worker = Worker(
        isolated_engine,
        "pytask_service.example_tasks:registry",
        executor=broken_executor,
    )
    worked = worker.run_once()

    assert worked is not None
    assert not worked.outcome.succeeded
    with Session(isolated_engine) as session:
        task = session.get(Task, task_id)
        assert task is not None
        assert task.status == TaskStatus.FAILED.value
        assert task.error is not None
        assert "process launch failed" in task.error
