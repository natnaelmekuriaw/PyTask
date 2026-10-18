from dataclasses import dataclass
from datetime import datetime


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


@dataclass(frozen=True, slots=True)
class ScheduleStats:
    total: int
    active: int
    paused: int
    due: int
    oldest_due_age_seconds: float | None


@dataclass(frozen=True, slots=True)
class MonitoringSnapshot:
    observed_at: datetime
    window_seconds: int
    window_start: datetime
    queue: QueueStats
    attempts: AttemptStats
    schedules: ScheduleStats
