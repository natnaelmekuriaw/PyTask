from datetime import UTC, datetime
from uuid import uuid4

import pytest

from pytask_service.api.cursors import InvalidCursor, Position, cursor_scope, decode_cursor, encode_cursor


def test_cursor_round_trip_preserves_ties_and_microseconds() -> None:
    position = Position(datetime(2027, 1, 1, microsecond=123456, tzinfo=UTC), uuid4())
    scope = cursor_scope("tasks", status="pending")
    assert decode_cursor(encode_cursor(position, scope), scope) == position


def test_cursor_cannot_be_reused_with_different_filters() -> None:
    position = Position(datetime.now(UTC), uuid4())
    cursor = encode_cursor(position, cursor_scope("tasks", status="pending"))
    with pytest.raises(InvalidCursor):
        decode_cursor(cursor, cursor_scope("tasks", status="failed"))
    with pytest.raises(InvalidCursor):
        decode_cursor(cursor, cursor_scope("schedules", status="pending"))
