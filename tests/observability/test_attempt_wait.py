from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from pytask_service.db.models import TaskAttempt
from pytask_service.monitoring import attempt_snapshot


@pytest.mark.parametrize("wait", [None, 0, 2.5])
def test_attempt_queue_wait_uses_its_own_eligibility(wait: float | None) -> None:
    started = datetime(2026, 10, 19, tzinfo=UTC)
    attempt = TaskAttempt(
        id=uuid4(), task_id=uuid4(), number=2, worker_id="worker",
        status="running", started_at=started,
        queued_at=None if wait is None else started - timedelta(seconds=wait),
    )
    details = attempt_snapshot(attempt)
    assert details["queue_wait_seconds"] == wait
    assert (details["queued_at"] is None) == (wait is None)


def test_reversed_timestamps_do_not_invent_a_zero_wait() -> None:
    started = datetime(2026, 10, 19, tzinfo=UTC)
    attempt = TaskAttempt(
        id=uuid4(), task_id=uuid4(), number=1, worker_id="worker",
        status="running", started_at=started,
        queued_at=started + timedelta(seconds=1),
    )
    assert attempt_snapshot(attempt)["queue_wait_seconds"] is None
