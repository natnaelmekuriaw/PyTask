from collections.abc import Callable
from uuid import UUID

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pytask_service.policy import TaskPolicy
from pytask_service.scheduling.definitions import (
    get_schedule,
    list_schedules,
    set_paused,
)

pytestmark = pytest.mark.integration


def test_created_schedule_keeps_arguments_and_execution_policy(
    isolated_engine: Engine, schedule_factory: Callable[..., UUID]
) -> None:
    schedule_id = schedule_factory(policy=TaskPolicy(5, 12, 2, 20))
    with Session(isolated_engine) as session:
        schedule = get_schedule(session, schedule_id)
        assert schedule is not None
        assert schedule.arguments == {"left": 1, "right": 2}
        assert (
            schedule.max_attempts,
            schedule.timeout_seconds,
            schedule.retry_base_seconds,
            schedule.retry_max_seconds,
        ) == (5, 12, 2, 20)
        assert schedule.last_scheduled_for is None
        assert not schedule.paused


def test_schedule_listing_has_stable_name_order_and_a_limit(
    isolated_engine: Engine, schedule_factory: Callable[..., UUID]
) -> None:
    schedule_factory(name="z-last")
    first = schedule_factory(name="a-first")
    with Session(isolated_engine) as session:
        rows = list_schedules(session, limit=1)
        assert [row.id for row in rows] == [first]


def test_pausing_twice_preserves_the_recurrence_cursor(
    isolated_engine: Engine, schedule_factory: Callable[..., UUID]
) -> None:
    schedule_id = schedule_factory()
    with Session(isolated_engine) as session, session.begin():
        schedule = set_paused(session, schedule_id, True)
        due, updated = schedule.next_run_at, schedule.updated_at
        same = set_paused(session, schedule_id, True)
        assert same.paused
        assert same.next_run_at == due
        assert same.updated_at == updated


def test_resuming_preserves_the_original_due_time(
    isolated_engine: Engine, schedule_factory: Callable[..., UUID]
) -> None:
    schedule_id = schedule_factory(paused=True)
    with Session(isolated_engine) as session, session.begin():
        before = get_schedule(session, schedule_id)
        assert before is not None
        due = before.next_run_at
        resumed = set_paused(session, schedule_id, False)
        assert not resumed.paused
        assert resumed.next_run_at == due


def test_duplicate_names_cannot_replace_existing_schedules(
    isolated_engine: Engine, schedule_factory: Callable[..., UUID]
) -> None:
    original = schedule_factory(name="daily-report")
    with pytest.raises(IntegrityError):
        schedule_factory(name="daily-report")
    with Session(isolated_engine) as session:
        assert [schedule.id for schedule in list_schedules(session)] == [original]


def test_resume_refreshes_a_definition_loaded_before_another_pause(
    isolated_engine: Engine, schedule_factory: Callable[..., UUID]
) -> None:
    schedule_id = schedule_factory()
    with Session(isolated_engine) as older, older.begin():
        loaded = get_schedule(older, schedule_id)
        assert loaded is not None and not loaded.paused
        with Session(isolated_engine) as newer, newer.begin():
            set_paused(newer, schedule_id, True)
        resumed = set_paused(older, schedule_id, False)
        assert not resumed.paused
    with Session(isolated_engine) as session:
        saved = get_schedule(session, schedule_id)
        assert saved is not None and not saved.paused
