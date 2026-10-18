from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select
from sqlalchemy.engine import Engine

from pytask_service.db.models import Task, TaskAttempt

pytestmark = pytest.mark.integration


def test_monitoring_upgrade_and_downgrade_preserve_attempt_history(
    isolated_engine: Engine,
) -> None:
    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    task_id, attempt_id = uuid4(), uuid4()
    with isolated_engine.begin() as connection:
        Task.metadata.drop_all(connection)
        config.attributes["connection"] = connection
        command.upgrade(config, "20261018_06")
        connection.execute(
            Task.__table__.insert().values(
                id=task_id,
                name="math.add",
                arguments={},
            )
        )
        connection.execute(
            TaskAttempt.__table__.insert().values(
                id=attempt_id,
                task_id=task_id,
                number=1,
                worker_id="legacy",
                status="succeeded",
                started_at=datetime(2026, 10, 18, 12, tzinfo=UTC),
                finished_at=datetime(2026, 10, 18, 12, 0, 1, tzinfo=UTC),
            )
        )
        command.upgrade(config, "head")
        command.check(config)
        row = connection.execute(
            select(TaskAttempt.id, TaskAttempt.queued_at).where(
                TaskAttempt.id == attempt_id
            )
        ).one()
        assert row.id == attempt_id and row.queued_at is None
        indexes = {
            item["name"] for item in inspect(connection).get_indexes("task_attempts")
        }
        assert {"ix_task_attempts_finished", "ix_task_attempts_started"} <= indexes
        command.downgrade(config, "20261018_06")
        assert "queued_at" not in {
            item["name"] for item in inspect(connection).get_columns("task_attempts")
        }
        assert connection.scalar(select(TaskAttempt.id)) == attempt_id
