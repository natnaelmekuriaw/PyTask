from collections.abc import Callable
from datetime import timedelta
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.clock import database_now
from pytask_service.db.models import Schedule, Task
from pytask_service.scheduling.dispatch import dispatch_due
from pytask_service.scheduling.definitions import get_schedule, list_occurrences
from pytask_service.policy import TaskPolicy

pytestmark = pytest.mark.integration


def test_dispatch_atomically_creates_a_task_and_advances_the_cursor(isolated_engine: Engine, schedule_factory: Callable[..., UUID]) -> None:
    schedule_id = schedule_factory()
    with Session(isolated_engine) as session, session.begin():
        tasks = dispatch_due(session)
        assert len(tasks) == 1 and tasks[0].created
        schedule = get_schedule(session, schedule_id)
        task = session.get(Task, tasks[0].id)
        assert schedule is not None and task is not None
        assert task.schedule_id == schedule_id
        assert task.scheduled_for == schedule.last_scheduled_for == tasks[0].scheduled_for
        assert schedule.next_run_at == task.scheduled_for + timedelta(seconds=60)
        assert task.status == "pending" and task.attempt_count == 0


def test_future_and_paused_schedules_do_not_dispatch(isolated_engine: Engine, schedule_factory: Callable[..., UUID]) -> None:
    with Session(isolated_engine) as session:
        future = database_now(session) + timedelta(days=1)
    schedule_factory(start_at=future)
    schedule_factory(paused=True)
    with Session(isolated_engine) as session, session.begin():
        assert dispatch_due(session) == []
        assert session.scalar(select(func.count()).select_from(Task)) == 0


def test_downtime_enqueues_only_the_latest_due_occurrence(isolated_engine: Engine, schedule_factory: Callable[..., UUID]) -> None:
    with Session(isolated_engine) as session:
        start = database_now(session) - timedelta(days=30, seconds=10)
    schedule_id = schedule_factory(start_at=start, interval_seconds=3600)
    with Session(isolated_engine) as session, session.begin():
        tasks = dispatch_due(session)
        assert len(tasks) == 1
        occurrence = tasks[0].scheduled_for
        assert occurrence == start + timedelta(days=30)
        schedule = get_schedule(session, schedule_id)
        assert schedule is not None and schedule.next_run_at > database_now(session)


def test_repeated_ticks_do_not_enqueue_the_same_occurrence(isolated_engine: Engine, schedule_factory: Callable[..., UUID]) -> None:
    schedule_factory()
    with Session(isolated_engine) as session, session.begin():
        first = dispatch_due(session)
    with Session(isolated_engine) as session, session.begin():
        assert dispatch_due(session) == []
        assert session.scalar(select(func.count()).select_from(Task)) == len(first) == 1


def test_each_occurrence_copies_its_schedule_policy(isolated_engine: Engine, schedule_factory: Callable[..., UUID]) -> None:
    schedule_factory(policy=TaskPolicy(7, 15, 2, 30))
    with Session(isolated_engine) as session, session.begin():
        task = session.get(Task, dispatch_due(session)[0].id)
        assert task is not None
        assert (task.max_attempts, task.timeout_seconds, task.retry_base_seconds, task.retry_max_seconds) == (7, 15, 2, 30)
