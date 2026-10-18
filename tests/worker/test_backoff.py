import pytest

from pytask_service.worker.backoff import retry_delay


@pytest.mark.parametrize("attempt, expected", [(1, 1), (2, 2), (3, 4), (10, 10)])
def test_backoff_grows_until_the_cap(attempt: int, expected: float) -> None:
    assert retry_delay(attempt, 1, 10, lambda: 1) == expected


def test_jitter_spreads_retries_inside_the_current_window() -> None:
    assert retry_delay(3, 1, 60, lambda: 0.25) == 1
    assert retry_delay(3, 1, 60, lambda: 0) == 0


def test_large_attempt_numbers_do_not_overflow() -> None:
    assert retry_delay(1000, 1, 60, lambda: 1) == 60


@pytest.mark.parametrize("base, cap", [(0, 1), (2, 1), (1, float("inf"))])
def test_backoff_rejects_invalid_bounds(base: float, cap: float) -> None:
    with pytest.raises(ValueError):
        retry_delay(1, base, cap)
