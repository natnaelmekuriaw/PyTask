from dataclasses import replace

import pytest
from sqlalchemy import text

from pytask_service.benchmarks import database
from pytask_service.benchmarks.namespace import new_schema_name
from pytask_service.benchmarks.recovery import run_recovery
from pytask_service.config import Settings

pytestmark = pytest.mark.integration


def test_crashed_worker_is_replaced_without_editing_lease_timestamps(
    isolated_engine, monkeypatch, options
):
    schema = new_schema_name()
    monkeypatch.setattr(database, "new_schema_name", lambda: schema)
    result = run_recovery(
        isolated_engine,
        Settings.from_env(),
        replace(options, case_timeout=60, task_timeout=15, recovery=True),
    )
    assert result.valid
    assert result.attempt_statuses == ("abandoned", "succeeded")
    assert result.elapsed_seconds is not None and result.elapsed_seconds > 0
    with isolated_engine.connect() as connection:
        assert (
            connection.scalar(
                text("SELECT count(*) FROM pg_namespace WHERE nspname = :schema"),
                {"schema": schema},
            )
            == 0
        )
