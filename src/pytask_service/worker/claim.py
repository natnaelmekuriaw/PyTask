import math
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import timedelta
from time import monotonic
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pytask_service.db.models import AttemptStatus, Task, TaskAttempt, TaskStatus
from pytask_service.worker.transactions import database_now


@dataclass(frozen=True, slots=True)
class ClaimedTask:
    id: UUID
    name: str
    arguments: dict[str, object]
    worker_id: str
    token: UUID = field(default_factory=uuid4)
    attempt_number: int = 1
    timeout_seconds: float = 300
    lease_deadline: float | None = None


def claim_next(
    session: Session, worker_id: str, lease_seconds: float = 30
) -> ClaimedTask | None:
    if not worker_id or len(worker_id) > 128:
        raise ValueError("worker_id must contain 1 to 128 characters")
    if not math.isfinite(lease_seconds) or lease_seconds <= 0:
        raise ValueError("lease_seconds must be positive and finite")

    task = session.scalar(
        select(Task)
        .where(
            Task.status == TaskStatus.PENDING.value,
            Task.available_at <= func.clock_timestamp(),
            Task.attempt_count < Task.max_attempts,
        )
        .order_by(Task.available_at, Task.created_at, Task.id)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    if task is None:
        return None

    lease_deadline = monotonic() + lease_seconds
    now = database_now(session)
    token = uuid4()
    task.status = TaskStatus.RUNNING.value
    task.started_at = now
    task.finished_at = None
    task.worker_id = worker_id
    task.claim_token = token
    task.lease_expires_at = now + timedelta(seconds=lease_seconds)
    task.attempt_count += 1
    task.result = None
    task.error = None
    session.add(
        TaskAttempt(
            id=token,
            task_id=task.id,
            number=task.attempt_count,
            queued_at=task.available_at,
            worker_id=worker_id,
            status=AttemptStatus.RUNNING.value,
            started_at=now,
        )
    )
    session.flush()
    return ClaimedTask(
        task.id,
        task.name,
        deepcopy(task.arguments),
        worker_id,
        token,
        task.attempt_count,
        task.timeout_seconds,
        lease_deadline,
    )
