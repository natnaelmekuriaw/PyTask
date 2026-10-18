from datetime import UTC, datetime
from uuid import uuid4

import pytest

from pytask_service.api.cursors import (
    InvalidCursor,
    Position,
    cursor_scope,
    decode_cursor,
    encode_cursor,
)


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


@pytest.mark.parametrize("raw", ["", "not.a.cursor", "é", "e30", "W10", "x" * 1025])
def test_invalid_cursor_shapes_have_one_public_error(raw: str) -> None:
    with pytest.raises(InvalidCursor, match="Invalid pagination cursor"):
        decode_cursor(raw, cursor_scope("tasks"))


def test_filter_scope_is_independent_of_keyword_order() -> None:
    assert cursor_scope("tasks", status="pending", name="math.add") == cursor_scope(
        "tasks", name="math.add", status="pending"
    )
