from datetime import UTC, datetime, timedelta

from pytask_service.db.models import Task, TaskStatus
from pytask_service.worker.transitions import fail_or_retry


def test_failure_schedules_retry_within_attempt_budget() -> None:
    now = datetime.now(UTC)
    task = Task(
        attempt_count=2, max_attempts=3, retry_base_seconds=1, retry_max_seconds=60
    )

    status = fail_or_retry(task, now, "failed", lambda: 1)

    assert status == TaskStatus.PENDING
    assert task.available_at == now + timedelta(seconds=2)
    assert task.finished_at is None
    assert task.claim_token is None
    assert task.lease_expires_at is None


def test_failure_finishes_task_when_attempts_are_exhausted() -> None:
    now = datetime.now(UTC)
    task = Task(
        attempt_count=3, max_attempts=3, retry_base_seconds=1, retry_max_seconds=60
    )

    status = fail_or_retry(task, now, "final failure")

    assert status == TaskStatus.FAILED
    assert task.finished_at == now
    assert task.error == "final failure"
