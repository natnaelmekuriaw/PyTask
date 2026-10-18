import random
from collections.abc import Callable
from datetime import datetime, timedelta

from pytask_service.db.models import Task, TaskStatus
from pytask_service.worker.backoff import retry_delay


def fail_or_retry(
    task: Task, now: datetime, error: str,
    random_value: Callable[[], float] = random.random,
) -> TaskStatus:
    task.result = None
    task.error = error
    task.claim_token = None
    task.lease_expires_at = None
    if task.attempt_count < task.max_attempts:
        delay = retry_delay(
            task.attempt_count, task.retry_base_seconds,
            task.retry_max_seconds, random_value,
        )
        task.status = TaskStatus.PENDING.value
        task.available_at = now + timedelta(seconds=delay)
        task.finished_at = None
        return TaskStatus.PENDING

    task.status = TaskStatus.FAILED.value
    task.finished_at = now
    return TaskStatus.FAILED
