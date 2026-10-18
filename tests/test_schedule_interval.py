from datetime import UTC, datetime, timedelta

import pytest

from pytask_service.scheduling.interval import (
    due_occurrence,
    next_occurrence,
    validate_interval,
)

START = datetime(2026, 10, 18, 12, tzinfo=UTC)


@pytest.mark.parametrize("seconds", [0, -1, True, 1.5, 31536001])
def test_intervals_reject_invalid_values(seconds: int) -> None:
    with pytest.raises(ValueError, match="Interval"):
        validate_interval(seconds)


def test_future_occurrence_is_not_due() -> None:
    assert due_occurrence(START, START - timedelta(microseconds=1), 60) is None


def test_exact_boundary_is_due() -> None:
    assert due_occurrence(START, START, 60) == START


def test_missed_occurrences_collapse_to_the_latest_due_instant() -> None:
    now = START + timedelta(days=30, seconds=17)
    assert due_occurrence(START, now, 60) == now - timedelta(seconds=17)


def test_tick_latency_does_not_shift_the_schedule_cadence() -> None:
    now = START + timedelta(seconds=125, microseconds=999)
    assert due_occurrence(START, now, 60) == START + timedelta(seconds=120)


def test_advancing_the_cursor_moves_past_the_selected_occurrence() -> None:
    now = START + timedelta(seconds=125)
    occurrence = due_occurrence(START, now, 60)
    assert occurrence is not None
    assert next_occurrence(occurrence, 60) == START + timedelta(seconds=180)


def test_cursor_overflow_has_an_actionable_error() -> None:
    with pytest.raises(ValueError, match="timestamp range"):
        next_occurrence(datetime.max.replace(tzinfo=UTC), 1)
