from dataclasses import replace

import pytest

from pytask_service.benchmarks.catalog import WorkItem
from pytask_service.benchmarks.observations import validate_results


def test_results_match_submission_order_even_when_observed_out_of_order(observation):
    identities = tuple(task.id for task in observation.tasks)
    items = tuple(WorkItem("benchmark.noop", {}, index) for index in range(2))
    validate_results(
        items,
        identities,
        replace(observation, tasks=tuple(reversed(observation.tasks))),
    )


def test_boolean_is_not_accepted_as_an_integer_result(observation):
    task = replace(observation.tasks[0], result=False)
    with pytest.raises(RuntimeError, match="unexpected_task_result"):
        validate_results(
            (WorkItem("benchmark.noop", {}, 0),),
            (task.id,),
            replace(observation, tasks=(task,)),
        )


def test_duplicate_observed_or_submitted_identities_fail(observation):
    task = observation.tasks[0]
    item = WorkItem("benchmark.noop", {}, 0)
    for identities, tasks in [
        ((task.id,), (task, task)),
        ((task.id, task.id), (task,)),
    ]:
        with pytest.raises(RuntimeError, match="invalid_result_population"):
            validate_results(
                (item,) * len(identities), identities, replace(observation, tasks=tasks)
            )
