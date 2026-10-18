from datetime import timedelta

import pytest
from sqlalchemy.engine import Engine

from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


def test_oldest_ready_age_ignores_creation_time_and_exhausted_tasks(
    isolated_engine: Engine,
) -> None:
    database = MonitoringDatabase(isolated_engine)
    database.task(
        created_at=database.now - timedelta(days=10),
        available_at=database.now - timedelta(seconds=30),
    )
    database.task(
        available_at=database.now - timedelta(days=1), attempt_count=3, max_attempts=3,
    )
    snapshot = database.read()
    expected = (snapshot.observed_at - database.now).total_seconds() + 30
    assert snapshot.queue.oldest_ready_age_seconds == pytest.approx(expected)
