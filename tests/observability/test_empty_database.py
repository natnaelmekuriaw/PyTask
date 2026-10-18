import pytest
from sqlalchemy.engine import Engine

from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


def test_empty_database_returns_zero_counts_and_unknown_ages(
    isolated_engine: Engine,
) -> None:
    snapshot = MonitoringDatabase(isolated_engine).read()
    assert snapshot.queue.total == snapshot.queue.ready == 0
    assert snapshot.queue.oldest_ready_age_seconds is None
    assert snapshot.attempts.execution.samples == 0
    assert snapshot.attempts.execution.mean_seconds is None
    assert snapshot.schedules.total == 0
    assert snapshot.schedules.oldest_due_age_seconds is None
