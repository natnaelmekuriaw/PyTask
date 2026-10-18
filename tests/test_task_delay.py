from datetime import UTC, datetime, timedelta

import pytest

from pytask_service.scheduling.delay import resolve_availability, validate_delay


@pytest.mark.parametrize("seconds", [-1, float("nan"), float("inf"), True, 31536001])
def test_invalid_delays_are_rejected(seconds: float) -> None:
    with pytest.raises(ValueError, match="Delay"):
        validate_delay(seconds)


def test_absolute_time_never_reads_the_database() -> None:
    when = datetime(2026, 10, 18, tzinfo=UTC)
    assert resolve_availability(None, run_at=when) == when
    assert resolve_availability(None) is None


def test_delay_and_absolute_time_are_mutually_exclusive() -> None:
    with pytest.raises(ValueError, match="either"):
        resolve_availability(None, run_at=datetime.now(UTC), delay=1)
