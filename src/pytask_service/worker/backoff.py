import math
import random
from collections.abc import Callable


def retry_delay(
    attempt_number: int,
    base_seconds: float,
    max_seconds: float,
    random_value: Callable[[], float] = random.random,
) -> float:
    if attempt_number < 1:
        raise ValueError("attempt_number must be positive")
    if not (0 < base_seconds <= max_seconds < math.inf):
        raise ValueError("Retry delays must be finite, positive, and ordered")
    doublings = math.log2(max_seconds) - math.log2(base_seconds)
    ceiling = (
        max_seconds
        if attempt_number - 1 >= doublings
        else math.ldexp(base_seconds, attempt_number - 1)
    )
    return ceiling * random_value()
