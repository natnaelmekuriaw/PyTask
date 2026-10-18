from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from pytask_service.db.models import Task

pytestmark = pytest.mark.integration


def test_scheduling_upgrade_preserves_standalone_tasks(isolated_engine: Engine) -> None:
    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    task_id = uuid4()
    with isolated_engine.begin() as connection:
        Task.metadata.drop_all(connection)
        config.attributes["connection"] = connection
        command.upgrade(config, "20261018_04")
        connection.execute(
            text(
                "INSERT INTO tasks (id, name, arguments) "
                "VALUES (:id, 'math.add', CAST(:arguments AS jsonb))"
            ),
            {"id": task_id, "arguments": '{"left": 1, "right": 2}'},
        )
        command.upgrade(config, "head")
        command.check(config)
        row = connection.execute(
            text("SELECT status, schedule_id, scheduled_for FROM tasks WHERE id = :id"),
            {"id": task_id},
        ).one()
        assert tuple(row) == ("pending", None, None)
        assert "schedules" in inspect(connection).get_table_names()
        command.downgrade(config, "20261018_04")
        assert "schedules" not in inspect(connection).get_table_names()
        assert "schedule_id" not in {
            column["name"] for column in inspect(connection).get_columns("tasks")
        }
        assert (
            connection.scalar(
                text("SELECT count(*) FROM tasks WHERE id = :id"), {"id": task_id}
            )
            == 1
        )
        assert "task_attempts" in inspect(connection).get_table_names()
