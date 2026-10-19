import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response, Security

from pytask_service.api.auth_dependencies import access
from pytask_service.api.dependencies import ResourcesDep, SessionDep
from pytask_service.api.errors import APIError
from pytask_service.api.schemas.monitoring import AttemptRead, TaskRead
from pytask_service.api.schemas.pages import AttemptPage, Page
from pytask_service.api.schemas.tasks import TaskSubmit
from pytask_service.api.task_queries import attempt_page, task_page
from pytask_service.db.models import TaskStatus
from pytask_service.monitoring import attempt_snapshot, task_snapshot
from pytask_service.observability.events import log_event
from pytask_service.tasks import get_task, submit_task

router = APIRouter(prefix="/tasks", tags=["Tasks"])
logger = logging.getLogger(__name__)


@router.get("", response_model=Page[TaskRead], summary="List tasks",
            dependencies=[Security(access, scopes=["tasks:read"])],
            openapi_extra={"x-required-scopes": ["tasks:read"]})
def list_tasks(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query(max_length=1024)] = None,
    status: TaskStatus | None = None,
    schedule_id: UUID | None = None,
    name: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
) -> Page[TaskRead]:
    with session.begin():
        page = task_page(
            session,
            limit=limit,
            cursor=cursor,
            status=status,
            schedule_id=schedule_id,
            name=name,
        )
        return Page(
            items=[TaskRead.model_validate(task_snapshot(task)) for task in page.items],
            next_cursor=page.next_cursor,
        )


@router.post(
    "", status_code=201, response_model=TaskRead, summary="Submit a registered task",
    dependencies=[Security(access, scopes=["tasks:submit"])],
    openapi_extra={"x-required-scopes": ["tasks:submit"]},
)
def create_task(
    body: TaskSubmit,
    response: Response,
    request: Request,
    session: SessionDep,
    resources: ResourcesDep,
) -> TaskRead:
    with session.begin():
        task_id = submit_task(
            session,
            resources.registry,
            body.name,
            body.arguments,
            policy=body.as_policy(),
            run_at=body.run_at,
            delay=body.delay_seconds,
        )
        task = get_task(session, task_id)
        if task is None:
            raise RuntimeError("Submitted task was not found in its transaction")
        result = TaskRead.model_validate(task_snapshot(task))
    log_event(logger, "task.submitted", task_id=task_id)
    response.headers["Location"] = request.url_for("read_task", task_id=task_id).path
    return result


@router.get("/{task_id}", response_model=TaskRead, summary="Inspect a task",
            dependencies=[Security(access, scopes=["tasks:read"])],
            openapi_extra={"x-required-scopes": ["tasks:read"]})
def read_task(task_id: UUID, session: SessionDep) -> TaskRead:
    with session.begin():
        task = get_task(session, task_id)
        if task is None:
            raise APIError(404, "task_not_found", "Task not found")
        return TaskRead.model_validate(task_snapshot(task))


@router.get(
    "/{task_id}/attempts",
    response_model=AttemptPage,
    summary="Read task execution history",
    dependencies=[Security(access, scopes=["tasks:read"])],
    openapi_extra={"x-required-scopes": ["tasks:read"]},
)
def read_attempts(
    task_id: UUID,
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    after: Annotated[int, Query(ge=0, le=1000)] = 0,
) -> AttemptPage:
    with session.begin():
        if get_task(session, task_id) is None:
            raise APIError(404, "task_not_found", "Task not found")
        items, next_after = attempt_page(session, task_id, limit=limit, after=after)
        return AttemptPage(
            items=[
                AttemptRead.model_validate(attempt_snapshot(item)) for item in items
            ],
            next_after=next_after,
        )
