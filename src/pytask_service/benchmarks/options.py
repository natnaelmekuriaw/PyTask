import math
from dataclasses import dataclass
from enum import StrEnum


class Workload(StrEnum):
    NOOP = "noop"
    SLEEP = "sleep"
    CHECKSUM = "checksum"


@dataclass(frozen=True, slots=True)
class BenchmarkOptions:
    tasks: int = 20
    workers: tuple[int, ...] = (1, 2, 4)
    repeat: int = 3
    warmup: int = 2
    workloads: tuple[Workload, ...] = tuple(Workload)
    case_timeout: float = 120
    task_timeout: float = 10
    poll_interval: float = 0.05
    sleep_ms: int = 20
    iterations: int = 10000
    recovery: bool = True

    def __post_init__(self) -> None:
        for name, low, high in (
            ("tasks", 1, 10000),
            ("repeat", 1, 10),
            ("warmup", 0, 1000),
            ("sleep_ms", 0, 1000),
            ("iterations", 1, 1000000),
        ):
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"{name} must be an integer from {low} to {high}")
        if (
            not isinstance(self.workers, tuple)
            or not 1 <= len(self.workers) <= 8
            or any(type(n) is not int or not 1 <= n <= 32 for n in self.workers)
            or len(set(self.workers)) != len(self.workers)
        ):
            raise ValueError("workers must contain 1 to 8 distinct counts from 1 to 32")
        if (
            not isinstance(self.workloads, tuple)
            or not self.workloads
            or any(not isinstance(item, Workload) for item in self.workloads)
            or len(set(self.workloads)) != len(self.workloads)
        ):
            raise ValueError("workloads must contain distinct supported workloads")
        for name, lower, upper in (
            ("case_timeout", 5, 3600),
            ("task_timeout", 1, 120),
            ("poll_interval", 0.01, 1),
        ):
            value = getattr(self, name)
            if (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or not lower <= value <= upper
            ):
                raise ValueError(f"{name} must be finite and from {lower} to {upper}")
        if type(self.recovery) is not bool:
            raise ValueError("recovery must be a boolean")
        budget = (
            (self.tasks + self.warmup)
            * self.repeat
            * len(self.workers)
            * len(self.workloads)
        )
        if budget > 100000:
            raise ValueError("Benchmark plan exceeds 100000 total tasks")
