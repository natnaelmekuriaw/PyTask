import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkerPolicy:
    lease_seconds: float = 30
    heartbeat_seconds: float = 10
    recovery_batch_size: int = 100

    def __post_init__(self) -> None:
        for name in ("lease_seconds", "heartbeat_seconds"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a positive finite number")
        if self.heartbeat_seconds > self.lease_seconds / 3:
            raise ValueError("heartbeat_seconds cannot exceed one third of the lease")
        if (
            type(self.recovery_batch_size) is not int
            or not 1 <= self.recovery_batch_size <= 1000
        ):
            raise ValueError("recovery_batch_size must be an integer from 1 to 1000")
