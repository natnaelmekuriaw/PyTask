from datetime import timedelta

import pytest
from sqlalchemy.engine import Engine

from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


def test_schedule_backlog_excludes_paused_and_future_occurrences(
    isolated_engine: Engine,
) -> None:
    database = MonitoringDatabase(isolated_engine)
    database.schedule()
    database.schedule(paused=True, next_run_at=database.now - timedelta(days=1))
    database.schedule(next_run_at=database.now + timedelta(hours=1))
    snapshot = database.read()
    schedules = snapshot.schedules
    assert (schedules.total, schedules.active, schedules.paused, schedules.due) == (3, 2, 1, 1)
    expected = (snapshot.observed_at - database.now).total_seconds() + 30
    assert schedules.oldest_due_age_seconds == pytest.approx(expected)
