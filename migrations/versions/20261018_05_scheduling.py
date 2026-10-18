"""Add recurring schedules and task occurrence identity.

Revision ID: 20261018_05
Revises: 20261018_04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261018_05"
down_revision: str | None = "20261018_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("task_name", sa.String(128), nullable=False),
        sa.Column("arguments", postgresql.JSONB(), nullable=False),
        sa.Column("interval_seconds", sa.Integer(), nullable=False),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paused", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_scheduled_for", sa.DateTime(timezone=True)),
        sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False),
        sa.Column("timeout_seconds", sa.Float(), server_default="300", nullable=False),
        sa.Column("retry_base_seconds", sa.Float(), server_default="1", nullable=False),
        sa.Column("retry_max_seconds", sa.Float(), server_default="60", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_schedules_name"),
        sa.CheckConstraint(
            "interval_seconds BETWEEN 1 AND 31536000", name="ck_schedules_interval"
        ),
        sa.CheckConstraint(
            "max_attempts BETWEEN 1 AND 1000", name="ck_schedules_max_attempts"
        ),
        sa.CheckConstraint("timeout_seconds > 0", name="ck_schedules_timeout"),
        sa.CheckConstraint(
            "retry_base_seconds > 0 AND retry_max_seconds >= retry_base_seconds",
            name="ck_schedules_retry_delays",
        ),
    )
    op.create_index("ix_schedules_due", "schedules", ["paused", "next_run_at", "id"])
    op.add_column("tasks", sa.Column("schedule_id", postgresql.UUID(as_uuid=True)))
    op.add_column("tasks", sa.Column("scheduled_for", sa.DateTime(timezone=True)))
    op.create_foreign_key(
        "fk_tasks_schedule_id",
        "tasks",
        "schedules",
        ["schedule_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_tasks_schedule_occurrence", "tasks", ["schedule_id", "scheduled_for"]
    )
    op.create_check_constraint(
        "ck_tasks_schedule_origin",
        "tasks",
        "(schedule_id IS NULL) = (scheduled_for IS NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_tasks_schedule_origin", "tasks", type_="check")
    op.drop_constraint("uq_tasks_schedule_occurrence", "tasks", type_="unique")
    op.drop_constraint("fk_tasks_schedule_id", "tasks", type_="foreignkey")
    op.drop_column("tasks", "scheduled_for")
    op.drop_column("tasks", "schedule_id")
    op.drop_index("ix_schedules_due", table_name="schedules")
    op.drop_table("schedules")
