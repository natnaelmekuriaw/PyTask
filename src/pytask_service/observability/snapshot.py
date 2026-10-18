from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QueueStats:
    total: int
    pending: int
    ready: int
    delayed: int
    retry_wait: int
    retry_ready: int
    exhausted_pending: int
    running: int
    expired_running: int
    unleased_running: int
    succeeded: int
    failed: int
    oldest_ready_age_seconds: float | None
