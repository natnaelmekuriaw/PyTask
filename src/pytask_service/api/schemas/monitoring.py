from datetime import datetime
from uuid import UUID

from pytask_service.api.schemas.base import APIModel
from pytask_service.db.models import AttemptStatus, TaskStatus


class TaskRead(APIModel):
    id: UUID
    name: str
    arguments: dict[str, object]
    status: TaskStatus
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    duration_seconds: float | None
    worker_id: str | None
    result: object | None
    error: str | None
    attempt_count: int
    max_attempts: int
    schedule_id: UUID | None
    scheduled_for: datetime | None
    timeout_seconds: float
    available_at: datetime | None
    lease_expires_at: datetime | None


class AttemptRead(APIModel):
    id: UUID
    task_id: UUID
    number: int
    worker_id: str
    status: AttemptStatus
    started_at: datetime
    finished_at: datetime | None
    duration_seconds: float | None
    error: str | None


class ScheduleRead(APIModel):
    id: UUID
    name: str
    task_name: str
    arguments: dict[str, object]
    interval_seconds: int
    next_run_at: datetime
    paused: bool
    created_at: datetime
    updated_at: datetime
    last_scheduled_for: datetime | None
    max_attempts: int
    timeout_seconds: float
    retry_base_seconds: float
    retry_max_seconds: float
