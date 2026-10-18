from datetime import timedelta

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.clock import database_now
from pytask_service.db.models import Task
from pytask_service.example_tasks import registry
from pytask_service.tasks import list_attempts, submit_task
from pytask_service.worker.claim import claim_next

pytestmark = pytest.mark.integration


def test_delayed_task_cannot_be_claimed_until_eligible(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        task_id = submit_task(
            session,
            registry,
            "math.add",
            {"left": 1, "right": 2},
            run_at=database_now(session) + timedelta(days=1),
        )
    with Session(isolated_engine) as session, session.begin():
        assert claim_next(session, "early-worker") is None
        assert list_attempts(session, task_id) == []
        task = session.get(Task, task_id)
        assert task is not None
        task.available_at = database_now(session) - timedelta(seconds=1)
    with Session(isolated_engine) as session, session.begin():
        claim = claim_next(session, "due-worker")
        assert claim is not None and claim.id == task_id and claim.attempt_number == 1


def test_relative_delay_is_bounded_by_database_timestamps(
    isolated_engine: Engine,
) -> None:
    with Session(isolated_engine) as session, session.begin():
        before = database_now(session)
        task_id = submit_task(
            session, registry, "math.add", {"left": 1, "right": 2}, delay=30.5
        )
        after = database_now(session)
        task = session.get(Task, task_id)
        assert task is not None
        assert (
            before + timedelta(seconds=30.5)
            <= task.available_at
            <= after + timedelta(seconds=30.5)
        )
        assert task.schedule_id is None and task.scheduled_for is None
