import logging

import pytest
from sqlalchemy.engine import Engine

from pytask_service.worker import service
from pytask_service.worker.outcome import TaskOutcome
from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


def test_failed_finalization_does_not_log_a_committed_outcome(
    isolated_engine: Engine,
    event_records: list[logging.LogRecord],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    MonitoringDatabase(isolated_engine).task()
    original = service.finish_task

    def fail_after_flush(session: object, claim: object, outcome: object) -> None:
        original(session, claim, outcome)
        raise RuntimeError("commit did not happen")

    monkeypatch.setattr(service, "finish_task", fail_after_flush)
    worker = service.Worker(
        isolated_engine,
        "pytask_service.example_tasks:registry",
        executor=lambda path, claim, cancel: TaskOutcome.success(3),
    )
    with pytest.raises(RuntimeError, match="commit did not happen"):
        worker.run_once()
    assert any(r.msg == "task.claimed" for r in event_records)
    assert not any(r.msg == "task.attempt_finished" for r in event_records)
