from datetime import timedelta

import pytest
from sqlalchemy.engine import Engine

from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


def test_outcomes_use_finish_time_and_retries_use_start_time(
    isolated_engine: Engine,
) -> None:
    database = MonitoringDatabase(isolated_engine)
    database.attempt(
        database.task(),
        number=2,
        started_at=database.now - timedelta(seconds=90),
    )
    database.attempt(
        database.task(),
        finished_at=database.now - timedelta(seconds=90),
        started_at=database.now - timedelta(seconds=100),
    )
    database.attempt(
        database.task(),
        number=2,
        started_at=database.now + timedelta(hours=1),
        finished_at=database.now + timedelta(hours=2),
    )
    snapshot = database.read(60)
    assert snapshot.attempts.succeeded == 1
    assert snapshot.attempts.retries_started == 0
    assert (snapshot.observed_at - snapshot.window_start).total_seconds() == 60
