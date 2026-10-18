import math
from datetime import timedelta

from sqlalchemy import func, update
from sqlalchemy.orm import Session

from pytask_service.db.models import Task, TaskStatus
from pytask_service.worker.claim import ClaimedTask


def renew_claim(session: Session, claim: ClaimedTask, lease_seconds: float) -> bool:
    if not math.isfinite(lease_seconds) or lease_seconds <= 0:
        raise ValueError("lease_seconds must be positive and finite")
    renewed = session.scalar(
        update(Task)
        .where(
            Task.id == claim.id,
            Task.status == TaskStatus.RUNNING.value,
            Task.claim_token == claim.token,
            Task.worker_id == claim.worker_id,
            Task.lease_expires_at > func.clock_timestamp(),
        )
        .values(lease_expires_at=func.clock_timestamp() + timedelta(seconds=lease_seconds))
        .returning(Task.id)
    )
    return renewed is not None
