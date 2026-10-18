import json
import sys

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service import cli
from pytask_service.db.models import Task
from pytask_service.example_tasks import registry
from pytask_service.tasks import submit_task
from pytask_service.worker.claim import claim_next
from pytask_service.worker.finish import finish_task
from pytask_service.worker.outcome import TaskOutcome
from pytask_service.worker.transactions import database_now


@pytest.mark.integration
def test_attempts_command_keeps_failure_then_success(
    isolated_engine: Engine, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with Session(isolated_engine) as session, session.begin():
        task_id = submit_task(session, registry, "math.add", {"left": 1, "right": 2})
    with Session(isolated_engine) as session, session.begin():
        first = claim_next(session, "worker-one")
    assert first is not None
    with Session(isolated_engine) as session, session.begin():
        finish_task(session, first, TaskOutcome.failure(ValueError("temporary")))
        task = session.get(Task, task_id)
        assert task is not None
        task.available_at = database_now(session)
    with Session(isolated_engine) as session, session.begin():
        second = claim_next(session, "worker-two")
    assert second is not None
    with Session(isolated_engine) as session, session.begin():
        finish_task(session, second, TaskOutcome.success(3))

    monkeypatch.setattr(cli, "build_engine", lambda settings: isolated_engine)
    monkeypatch.setattr(sys, "argv", ["pytask-service", "attempts", str(task_id)])
    assert cli.main() == 0
    attempts = json.loads(capsys.readouterr().out)
    assert [attempt["number"] for attempt in attempts] == [1, 2]
    assert [attempt["status"] for attempt in attempts] == ["failed", "succeeded"]
    assert "temporary" in attempts[0]["error"]
    assert all(attempt["finished_at"] for attempt in attempts)
