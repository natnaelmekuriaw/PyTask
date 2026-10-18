from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select
from sqlalchemy.engine import Engine

from pytask_service.db.models import Task

pytestmark = pytest.mark.integration


def test_api_index_upgrade_preserves_tasks_and_matches_metadata(
    isolated_engine: Engine,
) -> None:
    root = Path(__file__).resolve().parents[3]
    config = Config(str(root / "alembic.ini"))
    task_id = uuid4()
    with isolated_engine.begin() as connection:
        Task.metadata.drop_all(connection)
        config.attributes["connection"] = connection
        command.upgrade(config, "20261018_05")
        connection.execute(
            Task.__table__.insert().values(
                id=task_id, name="math.add", arguments={"left": 1, "right": 2}
            )
        )
        command.upgrade(config, "head")
        command.check(config)
        assert connection.scalar(select(Task.id).where(Task.id == task_id)) == task_id
        assert "ix_tasks_created_id" in {
            index["name"] for index in inspect(connection).get_indexes("tasks")
        }
        command.downgrade(config, "20261018_05")
        assert "ix_tasks_created_id" not in {
            index["name"] for index in inspect(connection).get_indexes("tasks")
        }
        assert connection.scalar(select(Task.id).where(Task.id == task_id)) == task_id
        assert {"tasks", "task_attempts", "schedules"} <= set(
            inspect(connection).get_table_names()
        )
