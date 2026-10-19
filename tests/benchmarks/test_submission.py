from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from pytask_service.benchmarks import submission
from pytask_service.benchmarks.catalog import WorkItem
from pytask_service.benchmarks.errors import BenchmarkFailure
from pytask_service.policy import TaskPolicy


def test_each_submission_gets_a_separate_transaction(monkeypatch):
    session_factory, submit, check = MagicMock(), MagicMock(), MagicMock()
    identities = (uuid4(), uuid4())
    submit.side_effect = identities
    monkeypatch.setattr(submission, "Session", session_factory)
    monkeypatch.setattr(submission, "submit_task", submit)
    items = (WorkItem("benchmark.noop", {"index": 1}, 1),) * 2
    policy = TaskPolicy(max_attempts=1)
    assert (
        submission.submit_batch(MagicMock(), items, policy, check_deadline=check)
        == identities
    )
    assert session_factory.call_count == check.call_count == 2
    assert session_factory.return_value.__enter__.return_value.begin.call_count == 2
    assert all(call.kwargs["policy"] is policy for call in submit.call_args_list)


def test_expired_deadline_prevents_the_next_transaction(monkeypatch):
    sessions = MagicMock()
    monkeypatch.setattr(submission, "Session", sessions)
    check = MagicMock(side_effect=BenchmarkFailure("deadline_exceeded"))
    with pytest.raises(BenchmarkFailure):
        submission.submit_batch(
            MagicMock(),
            (WorkItem("benchmark.noop", {}, 0),),
            TaskPolicy(),
            check_deadline=check,
        )
    sessions.assert_not_called()


def test_duplicate_returned_task_ids_are_rejected(monkeypatch):
    monkeypatch.setattr(submission, "Session", MagicMock())
    identity = uuid4()
    monkeypatch.setattr(submission, "submit_task", lambda *a, **kw: identity)
    items = (WorkItem("benchmark.noop", {}, 0),) * 2
    with pytest.raises(BenchmarkFailure, match="duplicate_submission_identity"):
        submission.submit_batch(
            MagicMock(), items, TaskPolicy(), check_deadline=lambda: None
        )
