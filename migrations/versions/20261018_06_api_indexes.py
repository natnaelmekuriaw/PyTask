"""Index API collection reads.

Revision ID: 20261018_06
Revises: 20261018_05
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261018_06"
down_revision: str | None = "20261018_05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_tasks_created_id", "tasks", ["created_at", "id"])
    op.create_index("ix_tasks_status_created_id", "tasks", ["status", "created_at", "id"])
    op.create_index("ix_tasks_schedule_created_id", "tasks", ["schedule_id", "created_at", "id"])
    op.create_index("ix_tasks_name_created_id", "tasks", ["name", "created_at", "id"])
    op.create_index("ix_schedules_created_id", "schedules", ["created_at", "id"])


def downgrade() -> None:
    op.drop_index("ix_schedules_created_id", table_name="schedules")
    for name in ("ix_tasks_name_created_id", "ix_tasks_schedule_created_id", "ix_tasks_status_created_id", "ix_tasks_created_id"):
        op.drop_index(name, table_name="tasks")
