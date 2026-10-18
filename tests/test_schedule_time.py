from datetime import UTC, datetime, timedelta, timezone

import pytest

from pytask_service.scheduling.time import as_utc, parse_timestamp


def test_timestamp_offsets_normalize_to_the_same_instant() -> None:
    expected = datetime(2026, 10, 18, 9, tzinfo=UTC)
    assert parse_timestamp("2026-10-18T12:00:00+03:00") == expected
    assert as_utc(expected.astimezone(timezone(timedelta(hours=-4)))) == expected


def test_naive_timestamps_are_rejected() -> None:
    with pytest.raises(ValueError, match="UTC offset"):
        as_utc(datetime(2026, 10, 18))
    with pytest.raises(ValueError, match="UTC offset"):
        parse_timestamp("2026-10-18T12:00:00")
