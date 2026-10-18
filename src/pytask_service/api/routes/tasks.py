from uuid import UUID

from fastapi import APIRouter, Response

from pytask_service.api.dependencies import ResourcesDep, SessionDep
from pytask_service.api.errors import APIError
from pytask_service.api.schemas.monitoring import TaskRead
from pytask_service.api.schemas.tasks import TaskSubmit
from pytask_service.monitoring import task_snapshot
from pytask_service.tasks import get_task, submit_task

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", status_code=201, response_model=TaskRead, summary="Submit a registered task")
def create_task(body: TaskSubmit, response: Response, session: SessionDep, resources: ResourcesDep) -> TaskRead:
    with session.begin():
        task_id = submit_task(session, resources.registry, body.name, body.arguments, policy=body.as_policy(), run_at=body.run_at, delay=body.delay_seconds)
        task = get_task(session, task_id)
        if task is None:
            raise RuntimeError("Submitted task was not found in its transaction")
        result = TaskRead.model_validate(task_snapshot(task))
    response.headers["Location"] = f"/api/v1/tasks/{task_id}"
    return result


@router.get("/{task_id}", response_model=TaskRead, summary="Inspect a task")
def read_task(task_id: UUID, session: SessionDep) -> TaskRead:
    with session.begin():
        task = get_task(session, task_id)
        if task is None:
            raise APIError(404, "task_not_found", "Task not found")
        return TaskRead.model_validate(task_snapshot(task))
