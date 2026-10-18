from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.sql import ColumnElement, Subquery

from pytask_service.db.models import AttemptStatus, TaskAttempt


def execution_aggregate(
    since: ColumnElement[datetime], now: ColumnElement[datetime]
) -> Subquery:
    duration = func.extract("epoch", TaskAttempt.finished_at - TaskAttempt.started_at)
    return select(
        func.count().label("execution_samples"),
        func.min(duration).label("execution_min"),
        func.avg(duration).label("execution_mean"),
        func.max(duration).label("execution_max"),
    ).where(
        TaskAttempt.finished_at >= since,
        TaskAttempt.finished_at <= now,
        TaskAttempt.finished_at >= TaskAttempt.started_at,
        TaskAttempt.status.in_([
            AttemptStatus.SUCCEEDED.value,
            AttemptStatus.FAILED.value,
            AttemptStatus.TIMED_OUT.value,
        ]),
    ).subquery("execution")


def wait_aggregate(
    since: ColumnElement[datetime], now: ColumnElement[datetime]
) -> Subquery:
    duration = func.extract("epoch", TaskAttempt.started_at - TaskAttempt.queued_at)
    return select(
        func.count().label("queue_wait_samples"),
        func.min(duration).label("queue_wait_min"),
        func.avg(duration).label("queue_wait_mean"),
        func.max(duration).label("queue_wait_max"),
    ).where(
        TaskAttempt.started_at >= since,
        TaskAttempt.started_at <= now,
        TaskAttempt.queued_at <= TaskAttempt.started_at,
    ).subquery("queue_wait")
