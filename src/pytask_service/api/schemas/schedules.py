from datetime import datetime
from typing import Self

from pydantic import ConfigDict, Field, field_validator, model_validator

from pytask_service.api.schemas.inputs import TaskInput, timestamp_input
from pytask_service.scheduling.definitions import validate_schedule_name
from pytask_service.scheduling.interval import next_occurrence


class ScheduleCreate(TaskInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "minute-add",
                    "task_name": "math.add",
                    "arguments": {"left": 1, "right": 2},
                    "interval_seconds": 60,
                    "paused": True,
                }
            ]
        }
    )
    name: str = Field(min_length=1, max_length=128)
    task_name: str = Field(min_length=1, max_length=128, pattern=r"^[a-z][a-z0-9_.-]*$")
    interval_seconds: int = Field(strict=True, ge=1, le=31536000)
    start_at: datetime | None = None
    paused: bool = Field(default=False, strict=True)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return validate_schedule_name(value)

    @field_validator("start_at", mode="before")
    @classmethod
    def normalize_time(cls, value: object) -> datetime | None:
        return None if value is None else timestamp_input(value)

    @model_validator(mode="after")
    def validate_cursor_range(self) -> Self:
        if self.start_at is not None:
            next_occurrence(self.start_at, self.interval_seconds)
        return self
