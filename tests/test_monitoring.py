from datetime import UTC, datetime, timedelta
from uuid import uuid4

from pytask_service.db.models import Task, TaskStatus
from pytask_service.monitoring import task_snapshot


def test_task_snapshot_includes_execution_duration() -> None:
    started_at = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
    task = Task(
        id=uuid4(),
        name="math.add",
        arguments={"left": 2, "right": 3},
        status=TaskStatus.SUCCEEDED.value,
        created_at=started_at - timedelta(seconds=5),
        started_at=started_at,
        finished_at=started_at + timedelta(milliseconds=250),
        worker_id="worker-one",
        result=5,
    )

    snapshot = task_snapshot(task)

    assert snapshot["duration_seconds"] == 0.25
    assert snapshot["result"] == 5
    assert snapshot["worker_id"] == "worker-one"


def test_pending_task_has_no_execution_duration() -> None:
    task = Task(
        id=uuid4(),
        name="math.add",
        arguments={},
        status=TaskStatus.PENDING.value,
        created_at=datetime.now(UTC),
    )

    snapshot = task_snapshot(task)

    assert snapshot["duration_seconds"] is None
    assert snapshot["started_at"] is None
    assert snapshot["finished_at"] is None
