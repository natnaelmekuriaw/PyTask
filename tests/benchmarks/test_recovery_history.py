from dataclasses import replace
from datetime import timedelta
from uuid import uuid4

import pytest

from pytask_service.benchmarks.records import Observation
from pytask_service.benchmarks.recovery_history import verify_recovery


def recovered(observation):
    task = replace(observation.tasks[0], attempt_count=2)
    first = replace(observation.attempts[0], status="abandoned")
    second = replace(first, id=uuid4(), number=2, status="succeeded")
    return Observation((task,), (second, first))


def test_recovery_requires_abandonment_followed_by_success(observation):
    assert verify_recovery(recovered(observation)) == ("abandoned", "succeeded")


@pytest.mark.parametrize(
    "field,value", [("number", 1), ("status", "failed"), ("task_id", uuid4())]
)
def test_invalid_recovery_attempts_fail(observation, field, value):
    history = recovered(observation)
    bad = replace(history.attempts[0], **{field: value})
    with pytest.raises(RuntimeError, match="invalid_recovery_history"):
        verify_recovery(replace(history, attempts=(bad, history.attempts[1])))


def test_recovery_requires_distinct_claim_tokens(observation):
    history = recovered(observation)
    second, first = history.attempts
    with pytest.raises(RuntimeError, match="invalid_recovery_history"):
        verify_recovery(
            replace(history, attempts=(replace(second, id=first.id), first))
        )


def test_recovery_rejects_reversed_attempt_timestamps(observation):
    history = recovered(observation)
    second, first = history.attempts
    bad = replace(second, finished_at=second.started_at - timedelta(seconds=1))
    with pytest.raises(RuntimeError, match="invalid_timestamps"):
        verify_recovery(replace(history, attempts=(bad, first)))
