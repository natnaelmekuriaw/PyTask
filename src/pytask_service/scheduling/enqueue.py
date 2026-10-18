from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from pytask_service.db.models import Schedule, Task, TaskStatus
from pytask_service.scheduling.time import as_utc


@dataclass(frozen=True, slots=True)
class ScheduledTask:
    id: UUID
    schedule_id: UUID
    scheduled_for: datetime
    created: bool = True


def enqueue_occurrence(session: Session, schedule: Schedule, occurrence: datetime) -> ScheduledTask:
    occurrence = as_utc(occurrence)
    task_id = session.scalar(
        insert(Task).values(
            id=uuid4(), name=schedule.task_name, arguments=schedule.arguments,
            status=TaskStatus.PENDING.value, available_at=occurrence,
            schedule_id=schedule.id, scheduled_for=occurrence, attempt_count=0,
            max_attempts=schedule.max_attempts, timeout_seconds=schedule.timeout_seconds,
            retry_base_seconds=schedule.retry_base_seconds, retry_max_seconds=schedule.retry_max_seconds,
        ).on_conflict_do_nothing(constraint="uq_tasks_schedule_occurrence").returning(Task.id)
    )
    created = task_id is not None
    if task_id is None:
        task_id = session.scalar(select(Task.id).where(Task.schedule_id == schedule.id, Task.scheduled_for == occurrence))
    if task_id is None:
        raise RuntimeError("Occurrence was not inserted and no existing task was found")
    return ScheduledTask(task_id, schedule.id, occurrence, created)
