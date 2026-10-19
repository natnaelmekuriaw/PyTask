from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from pytask_service.benchmarks.cases import plan_cases
from pytask_service.benchmarks.environment import Environment
from pytask_service.benchmarks.metrics import measure
from pytask_service.benchmarks.options import BenchmarkOptions, Workload
from pytask_service.benchmarks.records import AttemptRecord, Observation, TaskRecord
from pytask_service.benchmarks.report import BenchmarkReport
from pytask_service.benchmarks.results import CaseResult


@pytest.fixture
def observation() -> Observation:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    tasks, attempts = [], []
    for index in range(2):
        identity = uuid4()
        tasks.append(
            TaskRecord(
                identity, "succeeded", start, start + timedelta(seconds=3), 1, index
            )
        )
        attempts.append(
            AttemptRecord(
                uuid4(),
                identity,
                1,
                "succeeded",
                start,
                start + timedelta(seconds=1),
                start + timedelta(seconds=3),
            )
        )
    return Observation(tuple(tasks), tuple(attempts))


@pytest.fixture
def metrics(observation):
    return measure(observation, 4.0, 0.5)


@pytest.fixture
def options():
    return BenchmarkOptions(
        tasks=2,
        workers=(1,),
        repeat=1,
        warmup=0,
        workloads=(Workload.NOOP,),
        recovery=False,
    )


@pytest.fixture
def report(options, metrics):
    environment = Environment("3.12.0", "CPython", "test-platform", 4, {})
    results = tuple(CaseResult(case, metrics) for case in plan_cases(options))
    return BenchmarkReport(options, environment, "2026-01-01T00:00:00+00:00", results)
