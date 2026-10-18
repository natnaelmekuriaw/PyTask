from datetime import timedelta

import pytest
from sqlalchemy.engine import Engine

from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


def test_ready_delayed_retry_and_exhausted_counts_do_not_overlap(
    isolated_engine: Engine,
) -> None:
    database = MonitoringDatabase(isolated_engine)
    future = database.now + timedelta(hours=1)
    database.task()
    database.task(available_at=future)
    database.task(attempt_count=1, available_at=future)
    database.task(attempt_count=1)
    database.task(attempt_count=3, max_attempts=3)
    queue = database.read().queue
    assert queue.pending == 5
    assert (queue.ready, queue.delayed, queue.retry_wait) == (2, 1, 1)
    assert queue.retry_ready == 1 and queue.exhausted_pending == 1
    assert queue.ready + queue.delayed + queue.retry_wait + queue.exhausted_pending == 5
