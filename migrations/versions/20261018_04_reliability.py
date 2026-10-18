"""Add leases, retry policy, and attempt history.

Revision ID: 20261018_04
Revises: 20261018_03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261018_04"
down_revision: str | None = "20261018_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("available_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.add_column("tasks", sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("tasks", sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False))
    op.add_column("tasks", sa.Column("timeout_seconds", sa.Float(), server_default="300", nullable=False))
    op.add_column("tasks", sa.Column("retry_base_seconds", sa.Float(), server_default="1", nullable=False))
    op.add_column("tasks", sa.Column("retry_max_seconds", sa.Float(), server_default="60", nullable=False))
    op.add_column("tasks", sa.Column("claim_token", postgresql.UUID(as_uuid=True)))
    op.add_column("tasks", sa.Column("lease_expires_at", sa.DateTime(timezone=True)))
    op.execute("UPDATE tasks SET available_at = created_at")
    op.create_check_constraint("ck_tasks_max_attempts", "tasks", "max_attempts BETWEEN 1 AND 1000")
    op.create_check_constraint("ck_tasks_attempt_count", "tasks", "attempt_count BETWEEN 0 AND max_attempts")
    op.create_check_constraint("ck_tasks_timeout", "tasks", "timeout_seconds > 0")
    op.create_check_constraint("ck_tasks_retry_delays", "tasks", "retry_base_seconds > 0 AND retry_max_seconds >= retry_base_seconds")
    op.drop_index("ix_tasks_status_created_id", table_name="tasks")
    op.create_index("ix_tasks_ready", "tasks", ["status", "available_at", "created_at", "id"])
    op.create_index("ix_tasks_expired", "tasks", ["status", "lease_expires_at", "id"])
    op.create_table(
        "task_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("worker_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("error", sa.Text()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("task_id", "number", name="uq_task_attempts_task_number"),
        sa.CheckConstraint("number > 0", name="ck_task_attempts_number"),
    )
    _backfill_attempts()


def _backfill_attempts() -> None:
    op.execute("""
        INSERT INTO task_attempts
            (id, task_id, number, worker_id, status, started_at, finished_at, error)
        SELECT gen_random_uuid(), id, 1, COALESCE(worker_id, 'legacy'), status,
            COALESCE(started_at, created_at),
            CASE WHEN status = 'running' THEN NULL ELSE COALESCE(finished_at, clock_timestamp()) END,
            error
        FROM tasks WHERE status IN ('running', 'succeeded', 'failed')
    """)
    op.execute("""
        UPDATE tasks AS task SET attempt_count = 1,
            claim_token = CASE WHEN task.status = 'running' THEN attempt.id END,
            lease_expires_at = CASE WHEN task.status = 'running' THEN clock_timestamp() END
        FROM task_attempts AS attempt WHERE attempt.task_id = task.id AND attempt.number = 1
    """)


def downgrade() -> None:
    op.drop_table("task_attempts")
    op.drop_index("ix_tasks_expired", table_name="tasks")
    op.drop_index("ix_tasks_ready", table_name="tasks")
    op.create_index("ix_tasks_status_created_id", "tasks", ["status", "created_at", "id"])
    for name in ("ck_tasks_retry_delays", "ck_tasks_timeout", "ck_tasks_attempt_count", "ck_tasks_max_attempts"):
        op.drop_constraint(name, "tasks", type_="check")
    for name in ("lease_expires_at", "claim_token", "retry_max_seconds", "retry_base_seconds", "timeout_seconds", "max_attempts", "attempt_count", "available_at"):
        op.drop_column("tasks", name)
