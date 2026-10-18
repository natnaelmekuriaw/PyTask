from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from pytask_service.db.models import Task, TaskStatus


@dataclass(frozen=True, slots=True)
class ClaimedTask:
    id: UUID
    name: str
    arguments: dict[str, object]
    worker_id: str


def claim_next(session: Session, worker_id: str) -> ClaimedTask | None:
    task = session.scalar(
        select(Task)
        .where(Task.status == TaskStatus.PENDING.value)
        .order_by(Task.created_at, Task.id)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    if task is None:
        return None

    task.status = TaskStatus.RUNNING.value
    task.started_at = datetime.now(UTC)
    task.worker_id = worker_id
    session.flush()
    return ClaimedTask(task.id, task.name, deepcopy(task.arguments), worker_id)
