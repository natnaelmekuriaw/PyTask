from datetime import UTC, datetime, timedelta

from pytask_service.observability.snapshot import (
    AttemptStats,
    MonitoringSnapshot,
    QueueStats,
    ScheduleStats,
    TimingStats,
)


def empty_snapshot(window_seconds: int = 3600) -> MonitoringSnapshot:
    now = datetime(2026, 10, 19, 12, tzinfo=UTC)
    timing = TimingStats(0, None, None, None)
    return MonitoringSnapshot(
        now,
        window_seconds,
        now - timedelta(seconds=window_seconds),
        QueueStats(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None),
        AttemptStats(0, 0, 0, 0, 0, timing, timing),
        ScheduleStats(0, 0, 0, 0, None),
    )
