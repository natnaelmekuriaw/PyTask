from pytask_service.db.models import Task, TaskAttempt


def task_snapshot(task: Task) -> dict[str, object]:
    duration_seconds: float | None = None
    if task.started_at is not None and task.finished_at is not None:
        duration_seconds = (task.finished_at - task.started_at).total_seconds()

    return {
        "id": str(task.id),
        "name": task.name,
        "arguments": task.arguments,
        "status": task.status,
        "created_at": task.created_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
        "duration_seconds": duration_seconds,
        "worker_id": task.worker_id,
        "result": task.result,
        "error": task.error,
        "attempt_count": task.attempt_count,
        "max_attempts": task.max_attempts,
        "timeout_seconds": task.timeout_seconds,
        "available_at": task.available_at.isoformat() if task.available_at else None,
        "lease_expires_at": task.lease_expires_at.isoformat()
        if task.lease_expires_at
        else None,
    }


def attempt_snapshot(attempt: TaskAttempt) -> dict[str, object]:
    duration = None
    if attempt.finished_at is not None:
        duration = (attempt.finished_at - attempt.started_at).total_seconds()
    return {
        "id": str(attempt.id),
        "task_id": str(attempt.task_id),
        "number": attempt.number,
        "worker_id": attempt.worker_id,
        "status": attempt.status,
        "started_at": attempt.started_at.isoformat(),
        "finished_at": attempt.finished_at.isoformat() if attempt.finished_at else None,
        "duration_seconds": duration,
        "error": attempt.error,
    }
