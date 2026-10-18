from pytask_service.db.models import Task


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
    }
