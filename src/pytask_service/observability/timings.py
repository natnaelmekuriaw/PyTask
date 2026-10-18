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
