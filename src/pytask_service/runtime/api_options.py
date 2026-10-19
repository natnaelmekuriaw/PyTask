from dataclasses import dataclass

from pytask_service.env_options import integer_option


@dataclass(frozen=True, slots=True)
class APIOptions:
    graceful_seconds: int = 30
    concurrency: int = 100
    keep_alive_seconds: int = 5

    @classmethod
    def from_env(cls) -> "APIOptions":
        return cls(
            graceful_seconds=integer_option(
                "PYTASK_API_GRACEFUL_SECONDS", 30, minimum=1, maximum=300
            ),
            concurrency=integer_option(
                "PYTASK_API_CONCURRENCY", 100, minimum=1, maximum=10000
            ),
            keep_alive_seconds=integer_option(
                "PYTASK_API_KEEP_ALIVE_SECONDS", 5, minimum=1, maximum=60
            ),
        )
