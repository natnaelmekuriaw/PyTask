from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from pytask_service.db.base import Base


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "max_attempts BETWEEN 1 AND 1000", name="ck_tasks_max_attempts"
        ),
        CheckConstraint(
            "attempt_count BETWEEN 0 AND max_attempts", name="ck_tasks_attempt_count"
        ),
        CheckConstraint("timeout_seconds > 0", name="ck_tasks_timeout"),
        CheckConstraint(
            "retry_base_seconds > 0 AND retry_max_seconds >= retry_base_seconds",
            name="ck_tasks_retry_delays",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    arguments: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=TaskStatus.PENDING.value,
        server_default=TaskStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    worker_id: Mapped[str | None] = mapped_column(String(128))
    result: Mapped[object | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3, server_default="3"
    )
    timeout_seconds: Mapped[float] = mapped_column(
        Float, nullable=False, default=300, server_default="300"
    )
    retry_base_seconds: Mapped[float] = mapped_column(
        Float, nullable=False, default=1, server_default="1"
    )
    retry_max_seconds: Mapped[float] = mapped_column(
        Float, nullable=False, default=60, server_default="60"
    )
    claim_token: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


Index("ix_tasks_ready", Task.status, Task.available_at, Task.created_at, Task.id)
Index("ix_tasks_expired", Task.status, Task.lease_expires_at, Task.id)


class AttemptStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    ABANDONED = "abandoned"


class TaskAttempt(Base):
    __tablename__ = "task_attempts"
    __table_args__ = (
        UniqueConstraint("task_id", "number", name="uq_task_attempts_task_number"),
        CheckConstraint("number > 0", name="ck_task_attempts_number"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    worker_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    task_name: Mapped[str] = mapped_column(String(128), nullable=False)
    arguments: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paused: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
