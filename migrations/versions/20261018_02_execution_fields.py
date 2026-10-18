"""Store worker execution details.

Revision ID: 20261018_02
Revises: 20261018_01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261018_02"
down_revision: str | None = "20261018_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("started_at", sa.DateTime(timezone=True)))
    op.add_column("tasks", sa.Column("finished_at", sa.DateTime(timezone=True)))
    op.add_column("tasks", sa.Column("worker_id", sa.String(length=128)))
    op.add_column("tasks", sa.Column("result", postgresql.JSONB()))
    op.add_column("tasks", sa.Column("error", sa.Text()))


def downgrade() -> None:
    op.drop_column("tasks", "error")
    op.drop_column("tasks", "result")
    op.drop_column("tasks", "worker_id")
    op.drop_column("tasks", "finished_at")
    op.drop_column("tasks", "started_at")
