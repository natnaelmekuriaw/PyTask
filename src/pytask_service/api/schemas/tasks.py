from datetime import datetime
from typing import Self

from pydantic import Field, field_validator, model_validator

from pytask_service.api.schemas.inputs import TaskInput, timestamp_input


class TaskSubmit(TaskInput):
    name: str = Field(min_length=1, max_length=128, pattern=r"^[a-z][a-z0-9_.-]*$")
    run_at: datetime | None = None
    delay_seconds: float | None = Field(default=None, strict=True, ge=0, le=31536000, allow_inf_nan=False)

    @field_validator("run_at", mode="before")
    @classmethod
    def normalize_time(cls, value: object) -> datetime | None:
        return None if value is None else timestamp_input(value)

    @model_validator(mode="after")
    def validate_timing(self) -> Self:
        if self.run_at is not None and self.delay_seconds is not None:
            raise ValueError("Choose either run_at or delay_seconds")
        return self
