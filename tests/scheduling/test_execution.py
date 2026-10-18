from collections.abc import Callable
from datetime import timedelta
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.clock import database_now
from pytask_service.db.models import Task
from pytask_service.policy import TaskPolicy
from pytask_service.scheduling.dispatch import dispatch_due
from pytask_service.tasks import list_attempts
from pytask_service.worker.outcome import TaskOutcome
from pytask_service.worker.service import Worker

pytestmark = pytest.mark.integration


def test_scheduled_task_runs_through_the_worker_engine(isolated_engine: Engine, schedule_factory: Callable[..., UUID]) -> None:
    schedule_id = schedule_factory()
    with Session(isolated_engine) as session, session.begin():
        occurrence = dispatch_due(session)[0]
    worked = Worker(isolated_engine, "pytask_service.example_tasks:registry").run_once()
    assert worked is not None and worked.id == occurrence.id
    with Session(isolated_engine) as session:
        task = session.get(Task, worked.id)
        assert task is not None and task.result == 3 and task.status == "succeeded"
        assert task.schedule_id == schedule_id and task.scheduled_for == occurrence.scheduled_for
        assert len(list_attempts(session, task.id)) == 1


def test_retries_keep_one_task_for_the_scheduled_occurrence(isolated_engine: Engine, schedule_factory: Callable[..., UUID]) -> None:
    schedule_factory(policy=TaskPolicy(2, 10, 0.01, 0.01))
    with Session(isolated_engine) as session, session.begin():
        occurrence = dispatch_due(session)[0]
    outcomes = iter([TaskOutcome.failure(ValueError("retry")), TaskOutcome.success(3)])
    worker = Worker(isolated_engine, "pytask_service.example_tasks:registry", executor=lambda path, claim, cancel: next(outcomes))
    first = worker.run_once()
    assert first is not None and first.status == "pending"
    with Session(isolated_engine) as session, session.begin():
        task = session.get(Task, occurrence.id)
        assert task is not None
        task.available_at = database_now(session) - timedelta(seconds=1)
    second = worker.run_once()
    assert second is not None and second.status == "succeeded"
    with Session(isolated_engine) as session:
        task = session.get(Task, occurrence.id)
        assert task is not None and task.scheduled_for == occurrence.scheduled_for
        assert session.scalar(select(func.count()).select_from(Task)) == 1
        assert [attempt.status for attempt in list_attempts(session, task.id)] == ["failed", "succeeded"]
