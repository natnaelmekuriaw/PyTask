from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.orm import Session

from pytask_service.db.models import Task, TaskStatus
from pytask_service.worker.claim import ClaimedTask
from pytask_service.worker.outcome import TaskOutcome


class LostClaimError(RuntimeError):
    pass


def finish_task(session: Session, claim: ClaimedTask, outcome: TaskOutcome) -> None:
    status = TaskStatus.SUCCEEDED if outcome.succeeded else TaskStatus.FAILED
    updated = session.scalar(
        update(Task)
        .where(
            Task.id == claim.id,
            Task.status == TaskStatus.RUNNING.value,
            Task.worker_id == claim.worker_id,
        )
        .values(
            status=status.value,
            finished_at=datetime.now(UTC),
            result=outcome.result,
            error=outcome.error,
        )
        .returning(Task.id)
    )
    if updated is None:
        raise LostClaimError(f"Task claim is no longer current: {claim.id}")
