from uuid import UUID

from fastapi import APIRouter, Response

from pytask_service.api.dependencies import ResourcesDep, SessionDep
from pytask_service.api.errors import APIError
from pytask_service.api.schemas.monitoring import ScheduleRead
from pytask_service.api.schemas.schedules import ScheduleCreate
from pytask_service.scheduling.definitions import create_schedule, get_schedule
from pytask_service.scheduling.monitoring import schedule_snapshot

router = APIRouter(prefix="/schedules", tags=["Schedules"])


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
