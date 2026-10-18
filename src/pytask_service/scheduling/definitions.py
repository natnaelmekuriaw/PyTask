import re
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from pytask_service.db.clock import database_now
from pytask_service.db.models import Schedule
from pytask_service.db.transactions import bound_transaction
from pytask_service.policy import TaskPolicy
from pytask_service.registry import TaskRegistry
from pytask_service.scheduling.interval import next_occurrence, validate_interval
from pytask_service.scheduling.time import as_utc
from pytask_service.tasks import validate_task_arguments


def validate_schedule_name(name: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9_.-]{0,127}", name):
        raise ValueError(
            "Schedule name must start with a lowercase letter and contain at most "
            "128 lowercase letters, digits, dots, underscores, or hyphens"
        )
    return name


def create_schedule(
    session: Session,
    registry: TaskRegistry,
    name: str,
    task_name: str,
    arguments: object,
    *,
    interval_seconds: int,
    start_at: datetime | None = None,
    policy: TaskPolicy | None = None,
) -> Schedule:
    name = validate_schedule_name(name)
    interval_seconds = validate_interval(interval_seconds)
    arguments = validate_task_arguments(registry, task_name, arguments)
    policy = policy or TaskPolicy()
    when = as_utc(start_at) if start_at is not None else database_now(session)
    next_occurrence(when, interval_seconds)
    schedule = Schedule(
        id=uuid4(),
        name=name,
        task_name=task_name,
        arguments=arguments,
        interval_seconds=interval_seconds,
        next_run_at=when,
        paused=False,
        max_attempts=policy.max_attempts,
        timeout_seconds=policy.timeout_seconds,
        retry_base_seconds=policy.retry_base_seconds,
        retry_max_seconds=policy.retry_max_seconds,
    )
    session.add(schedule)
    session.flush()
    return schedule


def get_schedule(session: Session, schedule_id: UUID) -> Schedule | None:
    return session.get(Schedule, schedule_id)


def list_schedules(session: Session, *, limit: int = 100) -> list[Schedule]:
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("Limit must be an integer from 1 to 1000")
    return list(
        session.scalars(
            select(Schedule).order_by(Schedule.name, Schedule.id).limit(limit)
        )
    )


def set_paused(session: Session, schedule_id: UUID, paused: bool) -> Schedule:
    bound_transaction(session)
    schedule = session.scalar(
        select(Schedule).where(Schedule.id == schedule_id).with_for_update()
    )
    if schedule is None:
        raise ValueError(f"Schedule not found: {schedule_id}")
    if schedule.paused != paused:
        schedule.paused = paused
        schedule.updated_at = database_now(session)
        session.flush()
    return schedule
