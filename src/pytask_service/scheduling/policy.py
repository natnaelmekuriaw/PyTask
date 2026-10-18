import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SchedulerPolicy:
    batch_size: int = 100
    poll_interval: float = 1

    def __post_init__(self) -> None:
        if type(self.batch_size) is not int or not 1 <= self.batch_size <= 1000:
            raise ValueError("Batch size must be an integer from 1 to 1000")
        if not math.isfinite(self.poll_interval) or self.poll_interval <= 0:
            raise ValueError("Poll interval must be positive and finite")
