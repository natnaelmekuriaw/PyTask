from datetime import datetime, timedelta

from pytask_service.scheduling.time import as_utc

MAX_INTERVAL_SECONDS = 365 * 24 * 60 * 60


def validate_interval(seconds: int) -> int:
    if type(seconds) is not int or not 1 <= seconds <= MAX_INTERVAL_SECONDS:
        raise ValueError("Interval must be an integer from 1 to 31536000 seconds")
    return seconds


def due_occurrence(
    next_run_at: datetime, now: datetime, seconds: int
) -> datetime | None:
    interval = timedelta(seconds=validate_interval(seconds))
    due, now = as_utc(next_run_at), as_utc(now)
    if due > now:
        return None
    return due + ((now - due) // interval) * interval


def next_occurrence(occurrence: datetime, seconds: int) -> datetime:
    try:
        return as_utc(occurrence) + timedelta(seconds=validate_interval(seconds))
    except OverflowError as error:
        raise ValueError(
            "Next occurrence exceeds the supported timestamp range"
        ) from error
