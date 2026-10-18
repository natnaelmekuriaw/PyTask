from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pytask_service.db.clock import database_now
from pytask_service.db.models import Schedule
from pytask_service.db.transactions import bound_transaction
from pytask_service.scheduling.enqueue import ScheduledTask, enqueue_occurrence
from pytask_service.scheduling.interval import due_occurrence, next_occurrence
from pytask_service.scheduling.policy import SchedulerPolicy


def dispatch_due(session: Session, *, batch_size: int = 100) -> list[ScheduledTask]:
    SchedulerPolicy(batch_size=batch_size)
    bound_transaction(session)
    schedules = session.scalars(
        select(Schedule)
        .where(
            Schedule.paused.is_(False), Schedule.next_run_at <= func.clock_timestamp()
        )
        .order_by(Schedule.next_run_at, Schedule.id)
        .limit(batch_size)
        .with_for_update(skip_locked=True)
        .execution_options(populate_existing=True)
    ).all()
    if not schedules:
        return []
    now = database_now(session)
    tasks = []
    for schedule in schedules:
        occurrence = due_occurrence(
            schedule.next_run_at, now, schedule.interval_seconds
        )
        if occurrence is None:
            continue
        following = next_occurrence(occurrence, schedule.interval_seconds)
        tasks.append(enqueue_occurrence(session, schedule, occurrence))
        schedule.next_run_at = following
        schedule.last_scheduled_for = occurrence
        schedule.updated_at = now
    session.flush()
    return tasks
