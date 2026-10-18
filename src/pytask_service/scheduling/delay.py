import math
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from pytask_service.db.clock import database_now
from pytask_service.scheduling.interval import MAX_INTERVAL_SECONDS
from pytask_service.scheduling.time import as_utc


def validate_delay(seconds: float) -> float:
    if isinstance(seconds, bool) or not math.isfinite(seconds) or not 0 <= seconds <= MAX_INTERVAL_SECONDS:
        raise ValueError("Delay must be between 0 and 31536000 seconds")
    return seconds


def resolve_availability(
    session: Session, *, run_at: datetime | None = None, delay: float | None = None
) -> datetime | None:
    if run_at is not None and delay is not None:
        raise ValueError("Choose either run_at or delay")
    if run_at is not None:
        return as_utc(run_at)
    if delay is not None:
        seconds = validate_delay(delay)
        return database_now(session) + timedelta(seconds=seconds)
    return None
