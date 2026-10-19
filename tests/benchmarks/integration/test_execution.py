from dataclasses import replace

import pytest
from sqlalchemy import text

from pytask_service.benchmarks import database
from pytask_service.benchmarks.cases import CaseSpec
from pytask_service.benchmarks.execution import run_case
from pytask_service.benchmarks.namespace import new_schema_name
from pytask_service.benchmarks.options import Workload
from pytask_service.config import Settings

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("workers", [1, 2])
def test_real_workers_finish_exactly_one_attempt_per_benchmark_task(
    isolated_engine, monkeypatch, options, workers
):
    schema = new_schema_name()
    monkeypatch.setattr(database, "new_schema_name", lambda: schema)
    result = run_case(
        isolated_engine,
        Settings.from_env(),
        CaseSpec(Workload.NOOP, workers, 1),
        replace(options, tasks=3, warmup=1, case_timeout=60, task_timeout=15),
    )
    assert result.valid
    metrics = result.metrics
    assert metrics.submitted == metrics.succeeded == metrics.attempts == 3
    assert metrics.latency_seconds.samples == metrics.queue_wait_seconds.samples == 3
    assert metrics.throughput_per_second > 0
    with isolated_engine.connect() as connection:
        assert (
            connection.scalar(
                text("SELECT count(*) FROM pg_namespace WHERE nspname = :schema"),
                {"schema": schema},
            )
            == 0
        )
