from threading import Event
from uuid import uuid4

import pytest

from pytask_service.db.models import TaskStatus
from pytask_service.worker import service
from pytask_service.worker.claim import ClaimedTask
from pytask_service.worker.outcome import TaskOutcome
from pytask_service.worker.policy import WorkerPolicy
from tests.observability.test_stats_cli import FakeSession


def test_lease_renewal_runs_while_claim_event_destination_is_slow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    renewed = Event()
    claim_events: list[str] = []

    def slow_destination(logger: object, event: str, **fields: object) -> None:
        if event == "task.claimed":
            claim_events.append(event)
            assert renewed.wait(1), "claim logging started before lease protection"

    worker = service.Worker(
        object(),
        "pytask_service.example_tasks:registry",
        executor=lambda path, claim, cancel: TaskOutcome.success(3),
        policy=WorkerPolicy(lease_seconds=2, heartbeat_seconds=0.01),
    )
    monkeypatch.setattr(worker, "_renew", lambda claim: renewed.set() or True)
    monkeypatch.setattr(service, "log_event", slow_destination)
    monkeypatch.setattr(service, "Session", lambda engine: FakeSession())
    monkeypatch.setattr(service, "finish_task", lambda *args: TaskStatus.SUCCEEDED)
    claim = ClaimedTask(uuid4(), "math.add", {}, worker.worker_id)
    worked = worker._execute(claim)
    assert worked.status is TaskStatus.SUCCEEDED
    assert claim_events == ["task.claimed"]
