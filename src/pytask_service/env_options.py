import math
import os
import re


def integer_option(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    raw = raw.strip()
    if not re.fullmatch(r"[0-9]{1,10}", raw):
        raise ValueError(f"{name} must be an integer from {minimum} to {maximum}")
    value = int(raw)
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer from {minimum} to {maximum}")
    return value


def seconds_option(
    name: str, default: float, *, minimum: float, maximum: float
) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw.strip())
    except ValueError:
        raise ValueError(
            f"{name} must be finite and from {minimum:g} to {maximum:g}"
        ) from None
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be finite and from {minimum:g} to {maximum:g}")
    return value
