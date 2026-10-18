import logging

import pytest
from sqlalchemy.engine import Engine

from pytask_service.worker.outcome import TaskOutcome
from pytask_service.worker.service import Worker
from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


def test_worker_events_correlate_claims_with_committed_results(
    isolated_engine: Engine, event_records: list[logging.LogRecord],
) -> None:
    database = MonitoringDatabase(isolated_engine)
    task_id = database.task()
    worker = Worker(
        isolated_engine, "pytask_service.example_tasks:registry", worker_id="worker",
        executor=lambda path, claim, cancel: TaskOutcome.success({"private": "result"}),
    )
    worked = worker.run_once()
    assert worked is not None
    events = [r for r in event_records if r.msg in {"task.claimed", "task.attempt_finished"}]
    assert [r.msg for r in events] == ["task.claimed", "task.attempt_finished"]
    assert all(r.event_fields["task_id"] == str(task_id) for r in events)
    assert events[0].event_fields["attempt_id"] == events[1].event_fields["attempt_id"]
    assert events[1].event_fields["status"] == "succeeded"
    assert "private" not in repr([r.event_fields for r in events])
