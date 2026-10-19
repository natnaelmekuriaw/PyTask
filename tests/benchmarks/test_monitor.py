from unittest.mock import MagicMock

import pytest

from pytask_service.benchmarks import monitor
from pytask_service.benchmarks.errors import BenchmarkFailure


def test_wait_checks_deadline_and_worker_health_before_querying(monkeypatch):
    events = []
    deadline = MagicMock()
    deadline.check.side_effect = lambda: events.append("deadline")
    workers = MagicMock()
    workers.ensure_alive.side_effect = lambda: events.append("alive")

    def complete(*_):
        events.append("query")
        return True

    monkeypatch.setattr(monitor, "batch_complete", complete)
    monitor.wait_for_batch(MagicMock(), (), workers, deadline, 0.05)
    assert events == ["deadline", "alive", "query"]


def test_poll_sleep_never_exceeds_remaining_deadline(monkeypatch):
    deadline, workers = MagicMock(), MagicMock()
    deadline.remaining = 0.02
    complete = MagicMock(side_effect=[False, True])
    sleep = MagicMock()
    monkeypatch.setattr(monitor, "batch_complete", complete)
    monkeypatch.setattr(monitor, "sleep", sleep)
    monitor.wait_for_batch(MagicMock(), (), workers, deadline, 0.5)
    sleep.assert_called_once_with(0.02)


def test_deadline_failure_stops_queries_immediately(monkeypatch):
    deadline = MagicMock()
    deadline.check.side_effect = BenchmarkFailure("deadline_exceeded")
    complete = MagicMock()
    monkeypatch.setattr(monitor, "batch_complete", complete)
    with pytest.raises(BenchmarkFailure):
        monitor.wait_for_batch(MagicMock(), (), MagicMock(), deadline, 0.05)
    complete.assert_not_called()
