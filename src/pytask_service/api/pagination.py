from dataclasses import dataclass

from pytask_service.api.cursors import Position, encode_cursor
from pytask_service.db.models import Schedule, Task


@dataclass(frozen=True, slots=True)
class Records[T]:
    items: list[T]
    next_cursor: str | None


def validate_limit(limit: int) -> None:
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("Page limit must be an integer from 1 to 100")


def finish_page[T: (Task, Schedule)](rows: list[T], limit: int, scope: str) -> Records[T]:
    items = rows[:limit]
    cursor = None
    if len(rows) > limit:
        last = items[-1]
        cursor = encode_cursor(Position(last.created_at, last.id), scope)
    return Records(items, cursor)
