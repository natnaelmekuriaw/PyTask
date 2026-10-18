from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pytask_service.db.models import AttemptStatus, Task, TaskAttempt, TaskStatus
from pytask_service.worker.transactions import bound_lease_transaction, database_now
from pytask_service.worker.transitions import fail_or_retry


def recover_expired(session: Session, batch_size: int = 100) -> int:
    if type(batch_size) is not int or not 1 <= batch_size <= 1000:
        raise ValueError("Recovery batch_size must be an integer from 1 to 1000")
    bound_lease_transaction(session)
    tasks = session.scalars(
        select(Task)
        .where(
            Task.status == TaskStatus.RUNNING.value,
            Task.lease_expires_at <= func.clock_timestamp(),
        )
        .order_by(Task.lease_expires_at, Task.id)
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    ).all()
    if not tasks:
        return 0
    now = database_now(session)
    for task in tasks:
        attempt = session.get(TaskAttempt, task.claim_token)
        if attempt is None or attempt.status != AttemptStatus.RUNNING.value:
            raise RuntimeError(f"Missing running attempt for task {task.id}")
        attempt.status = AttemptStatus.ABANDONED.value
        attempt.finished_at = now
        attempt.error = "Worker lease expired"
        fail_or_retry(task, now, attempt.error)
    session.flush()
    return len(tasks)
