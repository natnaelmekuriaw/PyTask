from dataclasses import dataclass

from fastapi import Request
from sqlalchemy.engine import Engine

from pytask_service.registry import TaskRegistry


@dataclass(frozen=True, slots=True)
class APIResources:
    engine: Engine
    registry: TaskRegistry


def get_resources(request: Request) -> APIResources:
    resources = getattr(request.app.state, "resources", None)
    if not isinstance(resources, APIResources):
        raise RuntimeError("API lifespan has not started")
    return resources
