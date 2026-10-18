from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.sql import ColumnElement, Subquery

from pytask_service.db.models import AttemptStatus, TaskAttempt


def outcome_aggregate(
    since: ColumnElement[datetime], now: ColumnElement[datetime]
) -> Subquery:
    return select(
        *(
            func.count().filter(TaskAttempt.status == status.value).label(
                "attempt_" + status.value
            )
            for status in (
                AttemptStatus.SUCCEEDED,
                AttemptStatus.FAILED,
                AttemptStatus.TIMED_OUT,
                AttemptStatus.ABANDONED,
            )
        )
    ).where(
        TaskAttempt.finished_at >= since, TaskAttempt.finished_at <= now
    ).subquery("outcomes")


def retry_aggregate(
    since: ColumnElement[datetime], now: ColumnElement[datetime]
) -> Subquery:
    return select(func.count().label("retries_started")).where(
        TaskAttempt.started_at >= since,
        TaskAttempt.started_at <= now,
        TaskAttempt.number > 1,
    ).subquery("retries")
