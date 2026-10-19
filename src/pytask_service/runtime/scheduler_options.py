from dataclasses import dataclass

from pytask_service.env_options import integer_option, seconds_option


@dataclass(frozen=True, slots=True)
class SchedulerOptions:
    batch_size: int = 100
    poll_seconds: float = 1

    @classmethod
    def from_env(cls) -> "SchedulerOptions":
        return cls(
            batch_size=integer_option(
                "PYTASK_SCHEDULER_BATCH_SIZE", 100, minimum=1, maximum=1000
            ),
            poll_seconds=seconds_option(
                "PYTASK_SCHEDULER_POLL_SECONDS", 1, minimum=0.05, maximum=60
            ),
        )
