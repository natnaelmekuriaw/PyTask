import json
import sys
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service import cli
from pytask_service.db.models import Task, TaskStatus
from pytask_service.example_tasks import registry
from pytask_service.tasks import submit_task
from tests.worker.conftest import isolated_engine as isolated_engine


@pytest.mark.integration
def test_submitted_task_can_be_read_from_postgres(isolated_engine: Engine) -> None:
    with isolated_engine.connect() as connection:
        transaction = connection.begin()
        try:
            with Session(connection) as session:
                task_id = submit_task(
                    session, registry, "math.add", {"left": 2, "right": 3}
                )
            with Session(connection) as session:
                task = session.scalar(select(Task).where(Task.id == task_id))
                assert task is not None
                assert task.name == "math.add"
                assert task.arguments == {"left": 2, "right": 3}
                assert task.status == TaskStatus.PENDING.value
                assert task.created_at.tzinfo is not None
        finally:
            transaction.rollback()


@pytest.mark.integration
def test_cli_submit_and_status_round_trip(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_engine: Engine,
) -> None:
    monkeypatch.setattr(cli, "build_engine", lambda settings: isolated_engine)
    monkeypatch.setenv("PYTASK_REGISTRY", "pytask_service.example_tasks:registry")
    monkeypatch.setattr(
        sys,
        "argv",
        ["pytask-service", "submit", "math.add", "--args", '{"left":2,"right":3}'],
    )
    assert cli.main() == 0
    submitted = json.loads(capsys.readouterr().out)
    task_id = UUID(submitted["id"])

    monkeypatch.setattr(sys, "argv", ["pytask-service", "status", str(task_id)])
    assert cli.main() == 0
    details = json.loads(capsys.readouterr().out)
    assert details["id"] == str(task_id)
    assert details["status"] == TaskStatus.PENDING.value
    assert details["arguments"] == {"left": 2, "right": 3}
