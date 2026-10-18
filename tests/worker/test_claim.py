import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import Task, TaskStatus
from pytask_service.example_tasks import registry
from pytask_service.tasks import submit_task
from pytask_service.worker.claim import claim_next


@pytest.mark.integration
def test_claim_marks_task_running(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        task_id = submit_task(
            session, registry, "math.add", {"left": 2, "right": 3}
        )

    with Session(isolated_engine) as session, session.begin():
        claim = claim_next(session, "worker-one")

    assert claim is not None
    assert claim.id == task_id
    assert claim.name == "math.add"
    assert claim.arguments == {"left": 2, "right": 3}

    with Session(isolated_engine) as session:
        task = session.get(Task, task_id)
        assert task is not None
        assert task.status == TaskStatus.RUNNING.value
        assert task.worker_id == "worker-one"
        assert task.started_at is not None
