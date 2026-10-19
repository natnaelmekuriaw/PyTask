from dataclasses import replace
from uuid import uuid4

import pytest

from pytask_service.benchmarks.metrics import measure
from pytask_service.benchmarks.records import Observation


@pytest.mark.parametrize(
    "status,attempt_count", [("pending", 0), ("failed", 1), ("succeeded", 2)]
)
def test_unfinished_failed_or_retried_tasks_invalidate_baselines(
    observation, status, attempt_count
):
    task = replace(observation.tasks[0], status=status, attempt_count=attempt_count)
    with pytest.raises(RuntimeError, match="task_failed"):
        measure(replace(observation, tasks=(task, observation.tasks[1])), 4, 1)


def test_duplicate_and_empty_task_populations_fail(observation):
    for tasks in ((), (observation.tasks[0],) * 2):
        with pytest.raises(RuntimeError, match="invalid_task_population"):
            measure(Observation(tasks, observation.attempts), 4, 1)


@pytest.mark.parametrize(
    "field,value", [("task_id", uuid4()), ("number", 2), ("status", "abandoned")]
)
def test_unrelated_or_retried_attempts_invalidate_baselines(observation, field, value):
    bad = replace(observation.attempts[0], **{field: value})
    with pytest.raises(RuntimeError, match="invalid_attempt_history"):
        measure(replace(observation, attempts=(bad, observation.attempts[1])), 4, 1)


def test_duplicate_attempt_ids_fail(observation):
    first, second = observation.attempts
    duplicate = replace(second, id=first.id)
    with pytest.raises(RuntimeError, match="invalid_attempt_history"):
        measure(replace(observation, attempts=(first, duplicate)), 4, 1)
