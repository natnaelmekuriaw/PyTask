from dataclasses import dataclass

from pytask_service.env_options import integer_option, seconds_option


@dataclass(frozen=True, slots=True)
class DatabaseOptions:
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: float = 5
    pool_recycle: int = 1800
    connect_timeout: int = 5

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
