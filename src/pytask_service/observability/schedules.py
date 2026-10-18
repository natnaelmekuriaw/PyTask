from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.sql import ColumnElement, Subquery

from pytask_service.db.models import Schedule


def schedule_aggregate(now: ColumnElement[datetime]) -> Subquery:
    due = and_(Schedule.paused.is_(False), Schedule.next_run_at <= now)
    oldest = func.min(Schedule.next_run_at).filter(due)
    return select(
        func.count().label("schedule_total"),
        func.count().filter(Schedule.paused.is_(False)).label("active_schedules"),
        func.count().filter(Schedule.paused.is_(True)).label("paused_schedules"),
        func.count().filter(due).label("due_schedules"),
        func.extract("epoch", now - oldest).label("oldest_due_age_seconds"),
    ).subquery("schedules")
