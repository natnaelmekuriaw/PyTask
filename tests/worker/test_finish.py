import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import Task, TaskStatus
from pytask_service.example_tasks import registry
from pytask_service.policy import TaskPolicy
from pytask_service.tasks import submit_task
from pytask_service.worker.claim import claim_next
from pytask_service.worker.finish import LostClaimError, finish_task
from pytask_service.worker.outcome import TaskOutcome


@pytest.mark.integration
def test_successful_task_stores_result_and_finish_time(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        task_id = submit_task(session, registry, "math.add", {"left": 2, "right": 3})

    with Session(isolated_engine) as session, session.begin():
        claim = claim_next(session, "worker-one")
    assert claim is not None

    with Session(isolated_engine) as session, session.begin():
        finish_task(session, claim, TaskOutcome.success(5))

    with Session(isolated_engine) as session:
        task = session.get(Task, task_id)
        assert task is not None
        assert task.status == TaskStatus.SUCCEEDED.value
        assert task.result == 5
        assert task.error is None
        assert task.finished_at is not None
        assert task.started_at is not None
        assert task.finished_at >= task.started_at


@pytest.mark.integration
def test_failed_task_stores_error(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        task_id = submit_task(
            session,
            registry,
            "demo.fail",
            {"message": "expected failure"},
            policy=TaskPolicy(max_attempts=1),
        )

    with Session(isolated_engine) as session, session.begin():
        claim = claim_next(session, "worker-one")
    assert claim is not None

    with Session(isolated_engine) as session, session.begin():
        finish_task(session, claim, TaskOutcome.failure(RuntimeError("failed")))

    with Session(isolated_engine) as session:
        task = session.get(Task, task_id)
        assert task is not None
        assert task.status == TaskStatus.FAILED.value
        assert task.result is None
        assert task.error is not None
        assert "RuntimeError: failed" in task.error


@pytest.mark.integration
def test_stale_worker_cannot_finish_another_claim(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        task_id = submit_task(session, registry, "math.add", {"left": 1, "right": 2})

    with Session(isolated_engine) as session, session.begin():
        claim = claim_next(session, "worker-one")
    assert claim is not None

    with Session(isolated_engine) as session, session.begin():
        task = session.get(Task, task_id)
        assert task is not None
        task.worker_id = "worker-two"

    with Session(isolated_engine) as session, session.begin():
        with pytest.raises(LostClaimError):
            finish_task(session, claim, TaskOutcome.success(3))

    with Session(isolated_engine) as session:
        task = session.get(Task, task_id)
        assert task is not None
        assert task.status == TaskStatus.RUNNING.value
