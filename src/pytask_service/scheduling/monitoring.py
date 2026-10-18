from pytask_service.db.models import Schedule


def schedule_snapshot(schedule: Schedule) -> dict[str, object]:
    return {
        "id": str(schedule.id),
        "name": schedule.name,
        "task_name": schedule.task_name,
        "arguments": schedule.arguments,
        "interval_seconds": schedule.interval_seconds,
        "next_run_at": schedule.next_run_at.isoformat(),
        "paused": schedule.paused,
        "created_at": schedule.created_at.isoformat(),
        "updated_at": schedule.updated_at.isoformat(),
        "last_scheduled_for": schedule.last_scheduled_for.isoformat()
        if schedule.last_scheduled_for
        else None,
        "max_attempts": schedule.max_attempts,
        "timeout_seconds": schedule.timeout_seconds,
        "retry_base_seconds": schedule.retry_base_seconds,
        "retry_max_seconds": schedule.retry_max_seconds,
    }
