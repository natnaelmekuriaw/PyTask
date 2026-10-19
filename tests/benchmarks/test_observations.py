from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from pytask_service.benchmarks import observations


@pytest.mark.parametrize(
    "states,complete",
    [
        (["succeeded", "succeeded"], True),
        (["pending", "running"], False),
        (["running", "succeeded"], False),
    ],
)
def test_polling_requires_all_submitted_tasks_to_succeed(monkeypatch, states, complete):
    factory = MagicMock()
    factory.return_value.__enter__.return_value.scalars.return_value = states
    monkeypatch.setattr(observations, "Session", factory)
    assert observations.batch_complete(MagicMock(), (uuid4(), uuid4())) is complete


@pytest.mark.parametrize(
    "states,code",
    [
        (["succeeded"], "missing_tasks"),
        (["failed", "succeeded"], "task_failed"),
        (["cancelled", "succeeded"], "invalid_task_status"),
    ],
)
def test_polling_does_not_hide_missing_or_failed_tasks(monkeypatch, states, code):
    factory = MagicMock()
    factory.return_value.__enter__.return_value.scalars.return_value = states
    monkeypatch.setattr(observations, "Session", factory)
    with pytest.raises(RuntimeError, match=code):
        observations.batch_complete(MagicMock(), (uuid4(), uuid4()))
