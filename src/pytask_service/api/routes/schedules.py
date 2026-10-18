from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Response, Query

from pytask_service.api.dependencies import ResourcesDep, SessionDep
from pytask_service.api.errors import APIError
from pytask_service.api.schemas.monitoring import ScheduleRead
from pytask_service.api.schemas.schedules import ScheduleCreate
from pytask_service.scheduling.definitions import create_schedule, get_schedule, set_paused
from pytask_service.scheduling.monitoring import schedule_snapshot
from pytask_service.api.schedule_queries import schedule_page
from pytask_service.api.schemas.pages import Page

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.get("", response_model=Page[ScheduleRead], summary="List recurring schedules")
def listing(session: SessionDep, limit: Annotated[int, Query(ge=1, le=100)] = 50, cursor: Annotated[str | None, Query(max_length=1024)] = None, paused: bool | None = None, task_name: Annotated[str | None, Query(min_length=1, max_length=128)] = None) -> Page[ScheduleRead]:
    with session.begin():
        page = schedule_page(session, limit=limit, cursor=cursor, paused=paused, task_name=task_name)
        return Page(items=[ScheduleRead.model_validate(schedule_snapshot(item)) for item in page.items], next_cursor=page.next_cursor)


@router.post("", status_code=201, response_model=ScheduleRead, summary="Create a recurring schedule")
def create(body: ScheduleCreate, response: Response, session: SessionDep, resources: ResourcesDep) -> ScheduleRead:
    with session.begin():
        schedule = create_schedule(session, resources.registry, body.name, body.task_name, body.arguments, interval_seconds=body.interval_seconds, start_at=body.start_at, policy=body.as_policy(), paused=body.paused)
        result = ScheduleRead.model_validate(schedule_snapshot(schedule))
    response.headers["Location"] = f"/api/v1/schedules/{result.id}"
    return result


@router.get("/{schedule_id}", response_model=ScheduleRead, summary="Inspect a recurring schedule")
def read(schedule_id: UUID, session: SessionDep) -> ScheduleRead:
    with session.begin():
        schedule = get_schedule(session, schedule_id)
        if schedule is None:
            raise APIError(404, "schedule_not_found", "Schedule not found")
        return ScheduleRead.model_validate(schedule_snapshot(schedule))


def change_state(schedule_id: UUID, session: SessionDep, paused: bool) -> ScheduleRead:
    with session.begin():
        return ScheduleRead.model_validate(schedule_snapshot(set_paused(session, schedule_id, paused)))


@router.post("/{schedule_id}/pause", response_model=ScheduleRead, summary="Pause future dispatches")
def pause(schedule_id: UUID, session: SessionDep) -> ScheduleRead:
    return change_state(schedule_id, session, True)


@router.post("/{schedule_id}/resume", response_model=ScheduleRead, summary="Resume dispatch on the original cadence")
def resume(schedule_id: UUID, session: SessionDep) -> ScheduleRead:
    return change_state(schedule_id, session, False)
