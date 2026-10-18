from datetime import datetime

from pydantic import Field, field_validator

from pytask_service.api.schemas.policy import ExecutionPolicy
from pytask_service.arguments import normalize_arguments
from pytask_service.scheduling.time import as_utc, parse_timestamp


def timestamp_input(value: object) -> datetime:
    if isinstance(value, str):
        return parse_timestamp(value)
    if isinstance(value, datetime):
        return as_utc(value)
    raise ValueError("Timestamp must be ISO 8601 with a UTC offset")


class TaskInput(ExecutionPolicy):
    arguments: dict[str, object] = Field(default_factory=dict)

    @field_validator("arguments")
    @classmethod
    def validate_arguments(cls, value: dict[str, object]) -> dict[str, object]:
        return normalize_arguments(value)
