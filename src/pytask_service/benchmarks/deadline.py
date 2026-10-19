from collections.abc import Callable
from time import monotonic

from pytask_service.benchmarks.errors import BenchmarkFailure


class Deadline:
    def __init__(self, seconds: float, *, clock: Callable[[], float] = monotonic) -> None:
        self.clock = clock
        self.ends_at = clock() + seconds

    @property
    def remaining(self) -> float:
        return max(0.0, self.ends_at - self.clock())

    def check(self) -> None:
        if self.clock() >= self.ends_at:
            raise BenchmarkFailure("deadline_exceeded")

