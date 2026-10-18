from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.sql import ColumnElement, Subquery

from pytask_service.db.models import Task, TaskStatus


def queue_aggregate(now: ColumnElement[datetime]) -> Subquery:
    pending = Task.status == TaskStatus.PENDING.value
    running = Task.status == TaskStatus.RUNNING.value
    eligible = Task.attempt_count < Task.max_attempts
    ready = and_(pending, eligible, Task.available_at <= now)
    future = and_(pending, eligible, Task.available_at > now)
    oldest = func.min(Task.available_at).filter(ready)
    return select(
        func.count().label("task_total"),
        func.count().filter(pending).label("pending"),
        func.count().filter(ready).label("ready"),
        func.count().filter(and_(future, Task.attempt_count == 0)).label("delayed"),
        func.count().filter(and_(future, Task.attempt_count > 0)).label("retry_wait"),
        func.count().filter(and_(ready, Task.attempt_count > 0)).label("retry_ready"),
        func.count().filter(and_(pending, ~eligible)).label("exhausted_pending"),
        func.count().filter(running).label("running"),
        func.count()
        .filter(and_(running, Task.lease_expires_at <= now))
        .label("expired_running"),
        func.count()
        .filter(and_(running, Task.lease_expires_at.is_(None)))
        .label("unleased_running"),
        func.count()
        .filter(Task.status == TaskStatus.SUCCEEDED.value)
        .label("succeeded"),
        func.count().filter(Task.status == TaskStatus.FAILED.value).label("failed"),
        func.extract("epoch", now - oldest).label("oldest_ready_age_seconds"),
    ).subquery("queue")
