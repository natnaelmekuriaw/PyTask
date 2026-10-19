import math
from dataclasses import dataclass

from pytask_service.env_options import integer_option, seconds_option


@dataclass(frozen=True, slots=True)
class DatabaseOptions:
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: float = 5
    pool_recycle: int = 1800
    connect_timeout: int = 5

    def __post_init__(self) -> None:
        for name, minimum, maximum in (
            ("pool_size", 1, 100),
            ("max_overflow", 0, 100),
            ("pool_recycle", 30, 86400),
            ("connect_timeout", 1, 30),
        ):
            value = getattr(self, name)
            if type(value) is not int or not minimum <= value <= maximum:
                raise ValueError(
                    f"{name} must be an integer from {minimum} to {maximum}"
                )
        if (
            isinstance(self.pool_timeout, bool)
            or not math.isfinite(self.pool_timeout)
            or not 0.1 <= self.pool_timeout <= 60
        ):
            raise ValueError("pool_timeout must be finite and from 0.1 to 60")

    @classmethod
    def from_env(cls) -> "DatabaseOptions":
        return cls(
            pool_size=integer_option("PYTASK_DB_POOL_SIZE", 5, minimum=1, maximum=100),
            max_overflow=integer_option(
                "PYTASK_DB_MAX_OVERFLOW", 10, minimum=0, maximum=100
            ),
            pool_timeout=seconds_option(
                "PYTASK_DB_POOL_TIMEOUT", 5, minimum=0.1, maximum=60
            ),
            pool_recycle=integer_option(
                "PYTASK_DB_POOL_RECYCLE", 1800, minimum=30, maximum=86400
            ),
            connect_timeout=integer_option(
                "PYTASK_DB_CONNECT_TIMEOUT", 5, minimum=1, maximum=30
            ),
        )
