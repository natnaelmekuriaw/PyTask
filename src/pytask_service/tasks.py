import inspect
from uuid import UUID

from sqlalchemy.orm import Session

from pytask_service.arguments import InvalidTaskArguments, normalize_arguments
from pytask_service.db.models import Task, TaskStatus
from pytask_service.registry import TaskRegistry


def submit_task(
    session: Session, registry: TaskRegistry, name: str, arguments: object
) -> UUID:
    handler = registry.get(name)
    normalized = normalize_arguments(arguments)
    try:
        inspect.signature(handler).bind(**normalized)
    except TypeError as exc:
        raise InvalidTaskArguments(str(exc)) from exc

    task = Task(name=name, arguments=normalized, status=TaskStatus.PENDING.value)
    session.add(task)
    session.flush()
    return task.id
