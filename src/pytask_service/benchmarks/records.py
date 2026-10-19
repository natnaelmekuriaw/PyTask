from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TaskRecord:
    id: UUID
    status: str
    created_at: datetime
    finished_at: datetime | None
    attempt_count: int
    result: object = field(default=None, repr=False)


@dataclass(frozen=True, slots=True)
class AttemptRecord:
    id: UUID
    task_id: UUID
    number: int
    status: str
    queued_at: datetime | None
    started_at: datetime
    finished_at: datetime | None


@dataclass(frozen=True, slots=True)
class Observation:
    tasks: tuple[TaskRecord, ...]
    attempts: tuple[AttemptRecord, ...]
