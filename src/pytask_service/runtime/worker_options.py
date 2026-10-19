from dataclasses import dataclass

from pytask_service.env_options import seconds_option
from pytask_service.worker.policy import WorkerPolicy


@dataclass(frozen=True, slots=True)
class WorkerOptions:
    poll_seconds: float = 0.5
    lease_seconds: float = 30
    heartbeat_seconds: float = 10

    @classmethod
    def from_env(cls) -> "WorkerOptions":
        options = cls(
            poll_seconds=seconds_option(
                "PYTASK_WORKER_POLL_SECONDS", 0.5, minimum=0.05, maximum=60
            ),
            lease_seconds=seconds_option(
                "PYTASK_WORKER_LEASE_SECONDS", 30, minimum=1, maximum=3600
            ),
            heartbeat_seconds=seconds_option(
                "PYTASK_WORKER_HEARTBEAT_SECONDS", 10, minimum=0.05, maximum=1200
            ),
        )
        WorkerPolicy(options.lease_seconds, options.heartbeat_seconds)
        return options
