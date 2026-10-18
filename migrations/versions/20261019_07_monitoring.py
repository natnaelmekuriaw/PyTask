"""Record attempt eligibility and index observation windows.

Revision ID: 20261019_07
Revises: 20261018_06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261019_07"
down_revision: str | None = "20261018_06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("task_attempts", sa.Column("queued_at", sa.DateTime(timezone=True)))
    op.create_index("ix_task_attempts_finished", "task_attempts", ["finished_at"])
    op.create_index("ix_task_attempts_started", "task_attempts", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_task_attempts_started", table_name="task_attempts")
    op.drop_index("ix_task_attempts_finished", table_name="task_attempts")
    op.drop_column("task_attempts", "queued_at")
