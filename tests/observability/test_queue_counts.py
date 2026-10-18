import pytest
from sqlalchemy.engine import Engine

from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


def test_queue_counts_describe_all_retained_task_states(
    isolated_engine: Engine,
) -> None:
    database = MonitoringDatabase(isolated_engine)
    for status in ("pending", "running", "succeeded", "failed"):
        database.task(status=status)
    queue = database.read().queue
    assert queue.total == 4
    assert (queue.pending, queue.running, queue.succeeded, queue.failed) == (1, 1, 1, 1)
    assert queue.unleased_running == 1
