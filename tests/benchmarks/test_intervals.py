from datetime import UTC, datetime, timedelta, timezone, tzinfo

import pytest

from pytask_service.benchmarks.metrics import interval


def test_different_offsets_describe_the_same_instant():
    start = datetime(2026, 1, 1, 3, tzinfo=timezone(timedelta(hours=3)))
    assert interval(start, datetime(2026, 1, 1, 0, 0, 2, tzinfo=UTC)) == 2


@pytest.mark.parametrize(
    "start,end,code",
    [
        (None, datetime.now(UTC), "missing_timestamps"),
        (datetime(2026, 1, 1), datetime.now(UTC), "missing_timestamps"),
        (
            datetime(2026, 1, 2, tzinfo=UTC),
            datetime(2026, 1, 1, tzinfo=UTC),
            "invalid_timestamps",
        ),
    ],
)
def test_missing_naive_or_reversed_timestamps_fail(start, end, code):
    with pytest.raises(RuntimeError, match=code):
        interval(start, end)


def test_zero_duration_is_valid():
    instant = datetime(2026, 1, 1, tzinfo=UTC)
    assert interval(instant, instant) == 0


def test_repeated_local_hour_uses_elapsed_time_across_a_fold():
    class RepeatedHour(tzinfo):
        def utcoffset(self, value):
            return timedelta(hours=2 - value.fold)

        def dst(self, value):
            return timedelta(0)

    zone = RepeatedHour()
    start = datetime(2026, 10, 25, 2, 30, tzinfo=zone, fold=0)
    end = start.replace(fold=1)
    assert interval(start, end) == 3600
