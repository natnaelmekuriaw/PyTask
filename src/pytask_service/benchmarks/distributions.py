import math
from collections.abc import Iterable
from dataclasses import dataclass
from statistics import fmean


@dataclass(frozen=True, slots=True)
class Distribution:
    samples: int
    minimum: float | None
    mean: float | None
    p50: float | None
    p95: float | None
    p99: float | None
    maximum: float | None


def distribution(values: Iterable[float]) -> Distribution:
    ordered = sorted(values)
    if any(not math.isfinite(value) or value < 0 for value in ordered):
        raise ValueError("Timing samples must be finite and nonnegative")
    if not ordered:
        return Distribution(0, None, None, None, None, None, None)

    def percentile(q: float) -> float:
        position = (len(ordered) - 1) * q
        lower = math.floor(position)
        upper = math.ceil(position)
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)

    return Distribution(
        len(ordered), ordered[0], fmean(ordered), percentile(0.5),
        percentile(0.95), percentile(0.99), ordered[-1],
    )

