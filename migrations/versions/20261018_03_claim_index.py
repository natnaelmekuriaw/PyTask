"""Index pending task scans.

Revision ID: 20261018_03
Revises: 20261018_02
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20261018_03"
down_revision: str | None = "20261018_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_tasks_status_created_id", "tasks", ["status", "created_at", "id"]
    )


def downgrade() -> None:
    op.drop_index("ix_tasks_status_created_id", table_name="tasks")
