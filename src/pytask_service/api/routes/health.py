from typing import Literal

from fastapi import APIRouter
from sqlalchemy import select

from pytask_service.api.dependencies import SessionDep
from pytask_service.api.schemas.base import APIModel
from pytask_service.api.schemas.errors import ErrorResponse
from pytask_service.db.models import Schedule, Task, TaskAttempt
from pytask_service.db.transactions import bound_transaction

router = APIRouter(prefix="/health", tags=["Health"])


class HealthRead(APIModel):
    status: Literal["ok"] = "ok"


@router.get("/live", response_model=HealthRead, summary="Check process liveness")
def live() -> HealthRead:
    return HealthRead()


@router.get("/ready", response_model=HealthRead, responses={503: {"model": ErrorResponse}}, summary="Check database and schema access")
def ready(session: SessionDep) -> HealthRead:
    with session.begin():
        bound_transaction(session)
        for model in (Task, TaskAttempt, Schedule):
            session.execute(select(model).limit(0))
    return HealthRead()
