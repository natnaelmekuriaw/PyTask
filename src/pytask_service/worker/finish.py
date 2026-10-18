from sqlalchemy import select
from sqlalchemy.orm import Session

from pytask_service.db.models import AttemptStatus, Task, TaskAttempt, TaskStatus
from pytask_service.worker.claim import ClaimedTask
from pytask_service.worker.errors import LostClaimError
from pytask_service.worker.outcome import TaskOutcome
from pytask_service.worker.transactions import bound_lease_transaction, database_now
from pytask_service.worker.transitions import fail_or_retry


def finish_task(
    session: Session, claim: ClaimedTask, outcome: TaskOutcome
) -> TaskStatus:
    bound_lease_transaction(session)
    task = session.scalar(
        select(Task)
        .where(
            Task.id == claim.id,
            Task.status == TaskStatus.RUNNING.value,
            Task.worker_id == claim.worker_id,
            Task.claim_token == claim.token,
        )
        .with_for_update()
    )
    now = database_now(session)
    if task is None or task.lease_expires_at is None or task.lease_expires_at <= now:
        raise LostClaimError(f"Task claim is no longer current: {claim.id}")
    attempt = session.get(TaskAttempt, claim.token)
    if attempt is None or attempt.status != AttemptStatus.RUNNING.value:
        raise LostClaimError(f"Task attempt is no longer running: {claim.token}")

    attempt.finished_at = now
    attempt.error = outcome.error
    if outcome.succeeded:
        attempt.status = AttemptStatus.SUCCEEDED.value
        task.status = TaskStatus.SUCCEEDED.value
        task.result = outcome.result
        task.error = None
        task.finished_at = now
        task.claim_token = None
        task.lease_expires_at = None
        status = TaskStatus.SUCCEEDED
    else:
        attempt.status = (
            AttemptStatus.TIMED_OUT.value
            if outcome.timed_out
            else AttemptStatus.FAILED.value
        )
        status = fail_or_retry(
            task, now, outcome.error or "Task failed without an error message"
        )
    session.flush()
    return status
