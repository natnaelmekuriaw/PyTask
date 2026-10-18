from datetime import timedelta

import pytest
from sqlalchemy.engine import Engine

from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


def test_only_running_expired_leases_count_as_recoverable(isolated_engine: Engine) -> None:
    database = MonitoringDatabase(isolated_engine)
    past = database.now - timedelta(seconds=5)
    future = database.now + timedelta(hours=1)
    database.task(status="running", lease_expires_at=past)
    database.task(status="running", lease_expires_at=future)
    database.task(status="running")
    database.task(status="succeeded", lease_expires_at=past)
    queue = database.read().queue
    assert queue.running == 3
    assert queue.expired_running == 1 and queue.unleased_running == 1
