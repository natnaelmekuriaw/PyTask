from datetime import datetime

from pytask_service.api.schemas.base import APIModel
from pytask_service.observability.snapshot import (
    AttemptStats,
    QueueStats,
    ScheduleStats,
)


class MonitoringRead(APIModel):
    observed_at: datetime
    window_seconds: int
    window_start: datetime
    queue: QueueStats
    attempts: AttemptStats
    schedules: ScheduleStats
