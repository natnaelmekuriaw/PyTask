from datetime import timedelta

import pytest
from sqlalchemy.engine import Engine

from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


def test_execution_summary_uses_only_measured_terminal_attempts(
    isolated_engine: Engine,
) -> None:
    database = MonitoringDatabase(isolated_engine)
    end = database.now - timedelta(seconds=10)
    for duration, status in ((2, "succeeded"), (4, "timed_out")):
        database.attempt(
            database.task(), status=status, finished_at=end,
            started_at=end - timedelta(seconds=duration),
        )
    database.attempt(database.task(), status="abandoned")
    database.attempt(database.task(), started_at=database.now, finished_at=end)
    timing = database.read().attempts.execution
    assert timing.samples == 2
    assert (timing.min_seconds, timing.mean_seconds, timing.max_seconds) == (2, 3, 4)
