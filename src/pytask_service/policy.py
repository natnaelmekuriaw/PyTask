import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskPolicy:
    max_attempts: int = 3
    timeout_seconds: float = 300
    retry_base_seconds: float = 1
    retry_max_seconds: float = 60

    def __post_init__(self) -> None:
        if type(self.max_attempts) is not int or not 1 <= self.max_attempts <= 1000:
            raise ValueError("max_attempts must be an integer from 1 to 1000")
        for name in ("timeout_seconds", "retry_base_seconds", "retry_max_seconds"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a positive finite number")
        if self.retry_base_seconds > self.retry_max_seconds:
            raise ValueError("retry_base_seconds cannot exceed retry_max_seconds")
