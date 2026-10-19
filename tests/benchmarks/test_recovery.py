from contextlib import contextmanager
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from pytask_service.benchmarks import recovery
from pytask_service.benchmarks.records import Observation
from pytask_service.config import Settings


def test_recovery_uses_a_crashed_claim_and_two_attempt_policy(
    monkeypatch, options, observation
):
    events = []
    task = replace(observation.tasks[0], attempt_count=2, result=0)
    first = replace(observation.attempts[0], status="abandoned")
    second = replace(first, id=uuid4(), number=2, status="succeeded")
    history = Observation((task,), (first, second))

    @contextmanager
    def database(*args):
        try:
            yield SimpleNamespace(schema="isolated", connected_engine=MagicMock())
        finally:
            events.append("schema closed")

    @contextmanager
    def workers(*args, **kwargs):
        assert args[2] == 1
        events.append("replacement")
        try:
            yield MagicMock()
        finally:
            events.append("workers closed")

    def submit(engine, items, policy, **kwargs):
        assert policy.max_attempts == 2
        assert policy.retry_base_seconds == policy.retry_max_seconds == 0.01
        return (task.id,)

    def crash(*args):
        events.append("crash")

    times = iter((10, 14))
    monkeypatch.setattr(recovery, "BenchmarkDatabase", database)
    monkeypatch.setattr(recovery, "WorkerGroup", workers)
    monkeypatch.setattr(recovery, "submit_batch", submit)
    monkeypatch.setattr(recovery, "crash_worker", crash)
    monkeypatch.setattr(
        recovery, "wait_for_batch", lambda *args: events.append("completed")
    )
    monkeypatch.setattr(recovery, "observe", lambda *args: history)
    monkeypatch.setattr(recovery, "perf_counter", lambda: next(times))
    result = recovery.run_recovery(MagicMock(), Settings("unused"), options)
    assert result.valid
    assert result.elapsed_seconds == 4
    assert result.attempt_statuses == ("abandoned", "succeeded")
    assert events == [
        "crash",
        "replacement",
        "completed",
        "workers closed",
        "schema closed",
    ]
