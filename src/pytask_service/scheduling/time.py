from datetime import UTC, datetime


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timestamp must include a UTC offset")
    return value.astimezone(UTC)


def parse_timestamp(raw: str) -> datetime:
    try:
        value = datetime.fromisoformat(raw)
    except ValueError as error:
        raise ValueError("Timestamp must be ISO 8601 with a UTC offset") from error
    return as_utc(value)
