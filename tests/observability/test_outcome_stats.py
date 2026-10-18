import pytest
from sqlalchemy.engine import Engine

from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


def test_each_terminal_attempt_has_its_own_outcome_count(
    isolated_engine: Engine,
) -> None:
    database = MonitoringDatabase(isolated_engine)
    for status in ("succeeded", "failed", "timed_out", "abandoned"):
        database.attempt(database.task(), status=status)
    database.attempt(database.task(), status="running", finished_at=None)
    attempts = database.read().attempts
    assert (
        attempts.succeeded,
        attempts.failed,
        attempts.timed_out,
        attempts.abandoned,
    ) == (1, 1, 1, 1)
    assert attempts.execution.samples == 3
