from uuid import UUID

from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session

from pytask_service.api.cursors import cursor_scope, decode_cursor
from pytask_service.api.pagination import Records, finish_page, validate_limit
from pytask_service.db.models import Task, TaskAttempt, TaskStatus


def task_page(
    session: Session,
    *,
    limit: int = 50,
    cursor: str | None = None,
    status: TaskStatus | None = None,
    schedule_id: UUID | None = None,
    name: str | None = None,
) -> Records[Task]:
    validate_limit(limit)
    scope = cursor_scope(
        "tasks",
        status=status.value if status else None,
        schedule_id=str(schedule_id) if schedule_id else None,
        name=name,
    )
    query = select(Task)
    if status is not None:
        query = query.where(Task.status == status.value)
    if schedule_id is not None:
        query = query.where(Task.schedule_id == schedule_id)
    if name is not None:
        query = query.where(Task.name == name)
    if cursor is not None:
        position = decode_cursor(cursor, scope)
        query = query.where(
            tuple_(Task.created_at, Task.id) < tuple_(position.created_at, position.id)
        )
    rows = list(
        session.scalars(
            query.order_by(Task.created_at.desc(), Task.id.desc()).limit(limit + 1)
        )
    )
    return finish_page(rows, limit, scope)


def attempt_page(
    session: Session, task_id: UUID, *, limit: int = 50, after: int = 0
) -> tuple[list[TaskAttempt], int | None]:
    validate_limit(limit)
    if type(after) is not int or not 0 <= after <= 1000:
        raise ValueError("Attempt position must be an integer from 0 to 1000")
    rows = list(
        session.scalars(
            select(TaskAttempt)
            .where(TaskAttempt.task_id == task_id, TaskAttempt.number > after)
            .order_by(TaskAttempt.number)
            .limit(limit + 1)
        )
    )
    items = rows[:limit]
    return items, items[-1].number if len(rows) > limit else None
