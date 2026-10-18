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


def test_schedule_history_is_scoped_and_newest_first(isolated_engine: Engine, schedule_factory: Callable[..., UUID]) -> None:
    schedule_id = schedule_factory()
    other_id = schedule_factory()
    with Session(isolated_engine) as session, session.begin():
        dispatch_due(session)
        schedule = get_schedule(session, schedule_id)
        assert schedule is not None
        schedule.next_run_at -= timedelta(seconds=120)
    with Session(isolated_engine) as session, session.begin():
        dispatch_due(session)
        rows = list_occurrences(session, schedule_id, limit=1)
        assert len(rows) == 1 and rows[0].schedule_id == schedule_id
        assert len(list_occurrences(session, other_id)) == 1


def test_batch_limit_leaves_remaining_schedules_for_the_next_tick(isolated_engine: Engine, schedule_factory: Callable[..., UUID]) -> None:
    for _ in range(3):
        schedule_factory()
    with Session(isolated_engine) as session, session.begin():
        first = dispatch_due(session, batch_size=2)
    with Session(isolated_engine) as session, session.begin():
        second = dispatch_due(session, batch_size=2)
    assert len(first) == 2 and len(second) == 1
    assert len({task.schedule_id for task in [*first, *second]}) == 3


def test_rollback_discards_both_task_and_cursor_changes(isolated_engine: Engine, schedule_factory: Callable[..., UUID]) -> None:
    schedule_id = schedule_factory()
    with Session(isolated_engine) as session:
        transaction = session.begin()
        schedule = get_schedule(session, schedule_id)
        assert schedule is not None
        original = schedule.next_run_at
        assert len(dispatch_due(session)) == 1


def test_rewound_cursor_reuses_the_existing_occurrence_task(isolated_engine: Engine, schedule_factory: Callable[..., UUID]) -> None:
    schedule_id = schedule_factory()
    with Session(isolated_engine) as session, session.begin():
        first = dispatch_due(session)[0]
        schedule = get_schedule(session, schedule_id)
        assert schedule is not None
        schedule.next_run_at = first.scheduled_for
    with Session(isolated_engine) as session, session.begin():
        repeated = dispatch_due(session)[0]
        assert repeated.id == first.id and not repeated.created
        assert session.scalar(select(func.count()).select_from(Task)) == 1
        transaction.rollback()
    with Session(isolated_engine) as session, session.begin():
        schedule = get_schedule(session, schedule_id)
        assert schedule is not None and schedule.next_run_at == original
        assert session.scalar(select(func.count()).select_from(Task)) == 0
        assert len(dispatch_due(session)) == 1
