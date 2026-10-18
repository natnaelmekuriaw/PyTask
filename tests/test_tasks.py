from uuid import UUID

import pytest

from pytask_service.arguments import InvalidTaskArguments
from pytask_service.db.models import Task, TaskStatus
from pytask_service.registry import TaskRegistry, UnknownTaskError
from pytask_service.tasks import submit_task


class RecordingSession:
    def __init__(self) -> None:
        self.task: Task | None = None
        self.flushes = 0

    def add(self, task: Task) -> None:
        self.task = task

    def flush(self) -> None:
        self.flushes += 1


def test_submit_persists_a_pending_task_without_running_it() -> None:
    calls: list[tuple[int, int]] = []

    def add(left: int, right: int) -> int:
        calls.append((left, right))
        return left + right

    registry = TaskRegistry()
    registry.register("math.add", add)
    session = RecordingSession()
    arguments = {"left": 2, "right": 3}

    task_id = submit_task(session, registry, "math.add", arguments)
    arguments["left"] = 99

    assert isinstance(task_id, UUID)
    assert session.task is not None
    assert session.task.id == task_id
    assert session.task.arguments == {"left": 2, "right": 3}
    assert session.task.status == TaskStatus.PENDING.value
    assert session.flushes == 1
    assert calls == []


def test_submit_rejects_arguments_that_do_not_bind() -> None:
    registry = TaskRegistry()
    registry.register("math.add", lambda left, right: left + right)
    session = RecordingSession()

    with pytest.raises(InvalidTaskArguments, match="right"):
        submit_task(session, registry, "math.add", {"left": 2})

    assert session.task is None


def test_submit_rejects_unregistered_task() -> None:
    with pytest.raises(UnknownTaskError, match="missing"):
        submit_task(RecordingSession(), TaskRegistry(), "missing", {})
