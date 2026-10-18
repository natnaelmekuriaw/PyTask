from datetime import timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import Task, TaskAttempt
from pytask_service.example_tasks import registry
from pytask_service.tasks import submit_task
from pytask_service.worker.claim import claim_next
from pytask_service.worker.transactions import database_now


@pytest.mark.integration
def test_claim_records_lease_and_attempt_atomically(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        task_id = submit_task(session, registry, "math.add", {"left": 1, "right": 2})
    with Session(isolated_engine) as session, session.begin():
        claim = claim_next(session, "worker-one", lease_seconds=30)
    assert claim is not None
    with Session(isolated_engine) as session:
        task = session.get(Task, task_id)
        attempt = session.scalar(
            select(TaskAttempt).where(TaskAttempt.task_id == task_id)
        )
        assert task is not None and attempt is not None
        assert task.claim_token == claim.token == attempt.id
        assert task.attempt_count == attempt.number == 1
        assert task.started_at is not None and task.lease_expires_at is not None
        assert task.lease_expires_at - task.started_at == timedelta(seconds=30)


@pytest.mark.integration
def test_claim_waits_until_retry_is_due(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        task_id = submit_task(session, registry, "math.add", {"left": 1, "right": 2})
        task = session.get(Task, task_id)
        assert task is not None
        task.available_at = database_now(session) + timedelta(hours=1)
    with Session(isolated_engine) as session, session.begin():
        assert claim_next(session, "worker-one") is None


@pytest.mark.integration
def test_rolled_back_claim_does_not_consume_an_attempt(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        submit_task(session, registry, "math.add", {"left": 1, "right": 2})
    with Session(isolated_engine) as session:
        first = claim_next(session, "worker-one")
        session.rollback()
    with Session(isolated_engine) as session, session.begin():
        second = claim_next(session, "worker-two")
    assert first is not None and second is not None
    assert first.token != second.token
    assert second.attempt_number == 1
    with Session(isolated_engine) as session:
        assert session.get(TaskAttempt, first.token) is None
        assert session.get(TaskAttempt, second.token) is not None
