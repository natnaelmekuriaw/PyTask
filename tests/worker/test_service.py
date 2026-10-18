import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import Task, TaskStatus
from pytask_service.example_tasks import registry
from pytask_service.tasks import submit_task
from pytask_service.worker.outcome import TaskOutcome
from pytask_service.worker.service import Worker


@pytest.mark.integration
def test_worker_claims_executes_and_finishes_task(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        task_id = submit_task(session, registry, "math.add", {"left": 2, "right": 3})

    worker = Worker(
        isolated_engine,
        "pytask_service.example_tasks:registry",
        worker_id="worker-one",
        executor=lambda path, claim: TaskOutcome.success(5),
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
