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


@dataclass(frozen=True, slots=True)
class TimingStats:
    samples: int
    min_seconds: float | None
    mean_seconds: float | None
    max_seconds: float | None


@dataclass(frozen=True, slots=True)
class AttemptStats:
    succeeded: int
    failed: int
    timed_out: int
    abandoned: int
    retries_started: int
    execution: TimingStats
    queue_wait: TimingStats
