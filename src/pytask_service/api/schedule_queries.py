from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session

from pytask_service.api.cursors import cursor_scope, decode_cursor
from pytask_service.api.pagination import Records, finish_page, validate_limit
from pytask_service.db.models import Schedule


def schedule_page(
    session: Session,
    *,
    limit: int = 50,
    cursor: str | None = None,
    paused: bool | None = None,
    task_name: str | None = None,
) -> Records[Schedule]:
    validate_limit(limit)
    scope = cursor_scope("schedules", paused=paused, task_name=task_name)
    query = select(Schedule)
    if paused is not None:
        query = query.where(Schedule.paused == paused)
    if task_name is not None:
        query = query.where(Schedule.task_name == task_name)
    if cursor is not None:
        position = decode_cursor(cursor, scope)
        query = query.where(
            tuple_(Schedule.created_at, Schedule.id)
            < tuple_(position.created_at, position.id)
        )
    rows = list(
        session.scalars(
            query.order_by(Schedule.created_at.desc(), Schedule.id.desc()).limit(
                limit + 1
            )
        )
    )
    return finish_page(rows, limit, scope)
