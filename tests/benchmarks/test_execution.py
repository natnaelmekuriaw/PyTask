from contextlib import contextmanager
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from pytask_service.benchmarks import execution
from pytask_service.benchmarks.cases import CaseSpec
from pytask_service.benchmarks.errors import BenchmarkFailure
from pytask_service.benchmarks.options import Workload
from pytask_service.config import Settings


@pytest.fixture
def rig(monkeypatch, observation):
    events = []
    engine = MagicMock()

    @contextmanager
    def database(*args):
        events.append("schema ready")
        try:
            yield SimpleNamespace(schema="test", connected_engine=lambda: engine)
        finally:
            events.append("schema closed")

    @contextmanager
    def workers(*args, **kwargs):
        events.append("workers ready")
        try:
            yield MagicMock()
        finally:
            events.append("workers closed")

    def submit(engine, items, policy, **kwargs):
        events.append(("submit", len(items), policy.max_attempts))
        return tuple(task.id for task in observation.tasks)

    clock_values = iter((100.0, 101.0, 104.0))

    def clock():
        events.append("clock")
        return next(clock_values)

    def snapshot(*args):
        events.append("snapshot")
        return observation

    monkeypatch.setattr(execution, "BenchmarkDatabase", database)
    monkeypatch.setattr(execution, "WorkerGroup", workers)
    monkeypatch.setattr(execution, "submit_batch", submit)
    monkeypatch.setattr(
        execution, "wait_for_batch", lambda *args: events.append("complete")
    )
    monkeypatch.setattr(execution, "observe", snapshot)
    monkeypatch.setattr(execution, "perf_counter", clock)
    return events, engine


def test_warmup_and_startup_are_outside_the_measured_window(options, rig):
    events, engine = rig
    result = execution.run_case(
        engine,
        Settings("unused"),
        CaseSpec(Workload.NOOP, 1, 1),
        replace(options, warmup=2),
    )
    assert result.valid
    assert result.metrics.elapsed_seconds == 4
    assert result.metrics.submission_seconds == 1
    assert events[:5] == [
        "schema ready",
        "workers ready",
        ("submit", 2, 1),
        "complete",
        "snapshot",
    ]
    assert events[5:] == [
        "clock",
        ("submit", 2, 1),
        "clock",
        "complete",
        "clock",
        "snapshot",
        "workers closed",
        "schema closed",
    ]


def test_failed_warmup_closes_workers_before_the_schema(monkeypatch, options, rig):
    events, engine = rig

    def bad(*args):
        raise BenchmarkFailure("unexpected_task_result")

    monkeypatch.setattr(execution, "validate_results", bad)
    with pytest.raises(BenchmarkFailure):
        execution.run_case(
            engine,
            Settings("unused"),
            CaseSpec(Workload.NOOP, 1, 1),
            replace(options, warmup=2),
        )
    assert "clock" not in events
    assert events[-2:] == ["workers closed", "schema closed"]
