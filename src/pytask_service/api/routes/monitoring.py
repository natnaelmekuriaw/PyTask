from typing import Annotated

from fastapi import APIRouter, Query, Response, Security

from pytask_service.api.auth_dependencies import access
from pytask_service.api.dependencies import SessionDep
from pytask_service.api.schemas.stats import MonitoringRead
from pytask_service.observability.service import read_snapshot
from pytask_service.observability.window import (
    DEFAULT_WINDOW_SECONDS,
    MAX_WINDOW_SECONDS,
    MIN_WINDOW_SECONDS,
    ObservationWindow,
)

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("", response_model=MonitoringRead, summary="Read operational statistics",
            dependencies=[Security(access, scopes=["monitoring:read"])],
            openapi_extra={"x-required-scopes": ["monitoring:read"]})
def monitoring(
    session: SessionDep,
    response: Response,
    window_seconds: Annotated[
        int, Query(ge=MIN_WINDOW_SECONDS, le=MAX_WINDOW_SECONDS)
    ] = DEFAULT_WINDOW_SECONDS,
) -> MonitoringRead:
    with session.begin():
        snapshot = read_snapshot(session, ObservationWindow(window_seconds))
    response.headers["Cache-Control"] = "no-store"
    return MonitoringRead.model_validate(snapshot, from_attributes=True)
