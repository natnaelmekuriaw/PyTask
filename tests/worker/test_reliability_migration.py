from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from pytask_service.db.models import Task


@pytest.mark.integration
def test_upgrade_preserves_legacy_attempts_and_downgrades(
    isolated_engine: Engine,
) -> None:
    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    running_id, succeeded_id = uuid4(), uuid4()
    with isolated_engine.begin() as connection:
        Task.metadata.drop_all(connection)
        config.attributes["connection"] = connection
        command.upgrade(config, "20261018_03")
        connection.execute(
            text("""
            INSERT INTO tasks (id, name, arguments, status, started_at, worker_id)
            VALUES (:id, 'math.add', '{}'::jsonb, 'running',
                clock_timestamp(), 'old-worker')
        """),
            {"id": running_id},
        )
        connection.execute(
            text("""
            INSERT INTO tasks (id, name, arguments, status, started_at, finished_at)
            VALUES (:id, 'math.add', '{}'::jsonb, 'succeeded',
                clock_timestamp(), clock_timestamp())
        """),
            {"id": succeeded_id},
        )

        command.upgrade(config, "head")
        command.check(config)
        rows = (
            connection.execute(
                text("SELECT task_id, number, status FROM task_attempts")
            )
            .mappings()
            .all()
        )
        assert {(row["task_id"], row["number"], row["status"]) for row in rows} == {
            (running_id, 1, "running"),
            (succeeded_id, 1, "succeeded"),
        }
        running = (
            connection.execute(
                text(
                    "SELECT attempt_count, claim_token, "
                    "lease_expires_at <= clock_timestamp() AS expired "
                    "FROM tasks WHERE id = :id"
                ),
                {"id": running_id},
            )
            .mappings()
            .one()
        )
        assert running["attempt_count"] == 1
        assert running["claim_token"] is not None and running["expired"]

        command.downgrade(config, "20261018_03")
        assert "task_attempts" not in inspect(connection).get_table_names()
        assert "max_attempts" not in {
            column["name"] for column in inspect(connection).get_columns("tasks")
        }
