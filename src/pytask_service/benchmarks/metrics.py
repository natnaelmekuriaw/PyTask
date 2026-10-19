import math
from dataclasses import dataclass
from datetime import datetime

from pytask_service.benchmarks.distributions import Distribution, distribution
from pytask_service.benchmarks.errors import BenchmarkFailure
from pytask_service.benchmarks.records import Observation


@dataclass(frozen=True, slots=True)
class CaseMetrics:
    submitted: int
    succeeded: int
    failed: int
    attempts: int
    elapsed_seconds: float
    submission_seconds: float
    throughput_per_second: float
    submissions_per_second: float
    latency_seconds: Distribution
    queue_wait_seconds: Distribution
    attempt_seconds: Distribution


def interval(start: datetime | None, end: datetime | None) -> float:
    if (
        start is None
        or end is None
        or start.utcoffset() is None
        or end.utcoffset() is None
    ):
        raise BenchmarkFailure("missing_timestamps")
    value = (end - start).total_seconds()
    if value < 0 or not math.isfinite(value):
        raise BenchmarkFailure("invalid_timestamps")
    return value


def measure(observation: Observation, elapsed: float, submission: float) -> CaseMetrics:
    if (
        not math.isfinite(elapsed)
        or not math.isfinite(submission)
        or elapsed <= 0
        or submission <= 0
        or submission > elapsed
    ):
        raise BenchmarkFailure("invalid_elapsed_time")
    tasks, attempts = observation.tasks, observation.attempts
    if not tasks or len({task.id for task in tasks}) != len(tasks):
        raise BenchmarkFailure("invalid_task_population")
    if any(task.status != "succeeded" or task.attempt_count != 1 for task in tasks):
        raise BenchmarkFailure("task_failed")
    identities = {task.id for task in tasks}
    if (
        len(attempts) != len(tasks)
        or {attempt.task_id for attempt in attempts} != identities
        or len({attempt.id for attempt in attempts}) != len(attempts)
        or any(
            attempt.number != 1 or attempt.status != "succeeded" for attempt in attempts
        )
    ):
        raise BenchmarkFailure("invalid_attempt_history")
    return CaseMetrics(
        submitted=len(tasks),
        succeeded=len(tasks),
        failed=0,
        attempts=len(attempts),
        elapsed_seconds=elapsed,
        submission_seconds=submission,
        throughput_per_second=len(tasks) / elapsed,
        submissions_per_second=len(tasks) / submission,
        latency_seconds=distribution(
            interval(task.created_at, task.finished_at) for task in tasks
        ),
        queue_wait_seconds=distribution(
            interval(attempt.queued_at, attempt.started_at) for attempt in attempts
        ),
        attempt_seconds=distribution(
            interval(attempt.started_at, attempt.finished_at) for attempt in attempts
        ),
    )
