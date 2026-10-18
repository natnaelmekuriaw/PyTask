from datetime import UTC, datetime, timedelta

import pytest

from pytask_service.scheduling.interval import due_occurrence, validate_interval

START = datetime(2026, 10, 18, 12, tzinfo=UTC)


@pytest.mark.parametrize("seconds", [0, -1, True, 1.5, 31536001])
def test_intervals_reject_invalid_values(seconds: int) -> None:
    with pytest.raises(ValueError, match="Interval"):
        validate_interval(seconds)


def test_future_occurrence_is_not_due() -> None:
    assert due_occurrence(START, START - timedelta(microseconds=1), 60) is None


def test_exact_boundary_is_due() -> None:
    assert due_occurrence(START, START, 60) == START
