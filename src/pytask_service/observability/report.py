from datetime import datetime, timedelta

from sqlalchemy.engine import RowMapping

from pytask_service.observability.snapshot import (
    AttemptStats,
    MonitoringSnapshot,
    QueueStats,
    ScheduleStats,
    TimingStats,
)
from pytask_service.observability.window import ObservationWindow


def optional_seconds(row: RowMapping, key: str) -> float | None:
    value = row[key]
    return None if value is None else max(0.0, float(value))


def timing_stats(row: RowMapping, prefix: str) -> TimingStats:
    return TimingStats(
        samples=int(row[prefix + "_samples"]),
        min_seconds=optional_seconds(row, prefix + "_min"),
        mean_seconds=optional_seconds(row, prefix + "_mean"),
        max_seconds=optional_seconds(row, prefix + "_max"),
    )


def build_snapshot(row: RowMapping, window: ObservationWindow) -> MonitoringSnapshot:
    observed_at = row["observed_at"]
    if not isinstance(observed_at, datetime) or observed_at.utcoffset() is None:
        raise RuntimeError("PostgreSQL did not return an aware observation timestamp")
    return MonitoringSnapshot(
        observed_at=observed_at,
        window_seconds=window.seconds,
        window_start=observed_at - timedelta(seconds=window.seconds),
        queue=QueueStats(
            total=int(row["task_total"]),
            pending=int(row["pending"]),
            ready=int(row["ready"]),
            delayed=int(row["delayed"]),
            retry_wait=int(row["retry_wait"]),
            retry_ready=int(row["retry_ready"]),
            exhausted_pending=int(row["exhausted_pending"]),
            running=int(row["running"]),
            expired_running=int(row["expired_running"]),
            unleased_running=int(row["unleased_running"]),
            succeeded=int(row["succeeded"]),
            failed=int(row["failed"]),
            oldest_ready_age_seconds=optional_seconds(row, "oldest_ready_age_seconds"),
        ),
        attempts=AttemptStats(
            succeeded=int(row["attempt_succeeded"]),
            failed=int(row["attempt_failed"]),
            timed_out=int(row["attempt_timed_out"]),
            abandoned=int(row["attempt_abandoned"]),
            retries_started=int(row["retries_started"]),
            execution=timing_stats(row, "execution"),
            queue_wait=timing_stats(row, "queue_wait"),
        ),
        schedules=ScheduleStats(
            total=int(row["schedule_total"]),
            active=int(row["active_schedules"]),
            paused=int(row["paused_schedules"]),
            due=int(row["due_schedules"]),
            oldest_due_age_seconds=optional_seconds(row, "oldest_due_age_seconds"),
        ),
    )
