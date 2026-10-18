from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import Task, TaskStatus
from pytask_service.example_tasks import registry
from pytask_service.tasks import submit_task
from pytask_service.worker.claim import claim_next


@pytest.mark.integration
def test_empty_queue_returns_no_claim(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        assert claim_next(session, "worker-one") is None


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


@pytest.mark.integration
def test_competing_claim_skips_locked_task(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        task_id = submit_task(
            session, registry, "math.add", {"left": 1, "right": 2}
        )

    with Session(isolated_engine) as first, first.begin():
        claim = claim_next(first, "worker-one")
        assert claim is not None
        assert claim.id == task_id

        with Session(isolated_engine) as second, second.begin():
            assert claim_next(second, "worker-two") is None


@pytest.mark.integration
def test_oldest_pending_task_is_claimed_first(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        newer_id = submit_task(
            session, registry, "math.add", {"left": 3, "right": 4}
        )
        older_id = submit_task(
            session, registry, "math.add", {"left": 1, "right": 2}
        )
        older = session.get(Task, older_id)
        assert older is not None
        older.created_at = datetime.now(UTC) - timedelta(days=1)

    with Session(isolated_engine) as session, session.begin():
        claim = claim_next(session, "worker-one")

    assert claim is not None
    assert claim.id == older_id
    assert claim.id != newer_id
