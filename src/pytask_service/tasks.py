import inspect
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from pytask_service.arguments import InvalidTaskArguments, normalize_arguments
from pytask_service.db.models import Task, TaskAttempt, TaskStatus
from pytask_service.policy import TaskPolicy
from pytask_service.registry import TaskRegistry
from pytask_service.scheduling.delay import resolve_availability


def submit_task(
    session: Session,
    registry: TaskRegistry,
    name: str,
    arguments: object,
    *,
    policy: TaskPolicy | None = None,
    run_at: datetime | None = None,
    delay: float | None = None,
) -> UUID:
    policy = policy or TaskPolicy()
    normalized = validate_task_arguments(registry, name, arguments)
    available_at = resolve_availability(session, run_at=run_at, delay=delay)
    task = Task(
        id=uuid4(),
        name=name,
        arguments=normalized,
        status=TaskStatus.PENDING.value,
        attempt_count=0,
        max_attempts=policy.max_attempts,
        timeout_seconds=policy.timeout_seconds,
        retry_base_seconds=policy.retry_base_seconds,
        retry_max_seconds=policy.retry_max_seconds,
    )
    if available_at is not None:
        task.available_at = available_at
    session.add(task)
    session.flush()
    return task.id


def validate_task_arguments(
    registry: TaskRegistry, name: str, arguments: object
) -> dict[str, object]:
    handler = registry.get(name)
    normalized = normalize_arguments(arguments)
    try:
        inspect.signature(handler).bind(**normalized)
    except TypeError as exc:
        raise InvalidTaskArguments(str(exc)) from exc
    return normalized


def get_task(session: Session, task_id: UUID) -> Task | None:
    return session.get(Task, task_id)


def list_attempts(session: Session, task_id: UUID) -> list[TaskAttempt]:
    return list(
        session.scalars(
            select(TaskAttempt)
            .where(TaskAttempt.task_id == task_id)
            .order_by(TaskAttempt.number)
        )
    )
