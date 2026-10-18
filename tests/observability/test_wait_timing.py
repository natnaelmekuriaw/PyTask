from datetime import timedelta

import pytest
from sqlalchemy.engine import Engine

from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


def test_waiting_time_is_measured_per_claim_not_per_task(isolated_engine: Engine) -> None:
    database = MonitoringDatabase(isolated_engine)
    start = database.now - timedelta(seconds=10)
    for number, wait in ((1, 2), (2, 6)):
        database.attempt(
            database.task(), number=number, status="running", finished_at=None,
            started_at=start, queued_at=start - timedelta(seconds=wait),
        )
    attempts = database.read().attempts
    assert attempts.retries_started == 1
    timing = attempts.queue_wait
    assert timing.samples == 2
    assert (timing.min_seconds, timing.mean_seconds, timing.max_seconds) == (2, 4, 6)
