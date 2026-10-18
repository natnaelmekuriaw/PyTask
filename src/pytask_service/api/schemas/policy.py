from typing import Self

from pydantic import Field, model_validator

from pytask_service.api.schemas.base import APIModel
from pytask_service.policy import TaskPolicy


class ExecutionPolicy(APIModel):
    max_attempts: int = Field(default=3, strict=True, ge=1, le=1000)
    timeout_seconds: float = Field(default=300, strict=True, gt=0, le=31536000, allow_inf_nan=False)
    retry_base_seconds: float = Field(default=1, strict=True, gt=0, le=31536000, allow_inf_nan=False)
    retry_max_seconds: float = Field(default=60, strict=True, gt=0, le=31536000, allow_inf_nan=False)

    def as_policy(self) -> TaskPolicy:
        return TaskPolicy(self.max_attempts, self.timeout_seconds, self.retry_base_seconds, self.retry_max_seconds)

    @model_validator(mode="after")
    def validate_backoff(self) -> Self:
        self.as_policy()
        return self
