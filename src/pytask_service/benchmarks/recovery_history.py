from pytask_service.benchmarks.errors import BenchmarkFailure
from pytask_service.benchmarks.metrics import interval
from pytask_service.benchmarks.records import Observation


def verify_recovery(observed: Observation) -> tuple[str, ...]:
    if len(observed.tasks) != 1 or len(observed.attempts) != 2:
        raise BenchmarkFailure("invalid_recovery_population")
    task = observed.tasks[0]
    attempts = sorted(observed.attempts, key=lambda item: item.number)
    if (
        task.status != "succeeded" or task.attempt_count != 2
        or [attempt.number for attempt in attempts] != [1, 2]
        or [attempt.status for attempt in attempts] != ["abandoned", "succeeded"]
        or any(attempt.task_id != task.id for attempt in attempts)
        or attempts[0].id == attempts[1].id
    ):
        raise BenchmarkFailure("invalid_recovery_history")
    interval(task.created_at, task.finished_at)
    for attempt in attempts:
        interval(attempt.queued_at, attempt.started_at)
        interval(attempt.started_at, attempt.finished_at)
    return tuple(attempt.status for attempt in attempts)

