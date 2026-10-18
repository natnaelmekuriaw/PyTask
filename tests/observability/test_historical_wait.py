from datetime import timedelta

import pytest
from sqlalchemy.engine import Engine

from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


def test_unknown_and_reversed_eligibility_times_are_not_samples(
    isolated_engine: Engine,
) -> None:
    database = MonitoringDatabase(isolated_engine)
    database.attempt(database.task(), queued_at=None)
    database.attempt(
        database.task(),
        queued_at=database.now,
        started_at=database.now - timedelta(seconds=1),
    )
    attempts = database.read().attempts
    assert attempts.succeeded == 2
    assert attempts.queue_wait.samples == 0
    assert attempts.queue_wait.mean_seconds is None
