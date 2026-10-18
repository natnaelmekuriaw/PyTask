from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.engine import Engine

from pytask_service.api.resources import APIResources
from pytask_service.api.handlers import register_errors
from pytask_service.config import Settings
from pytask_service.db.engine import build_engine
from pytask_service.registry import TaskRegistry, load_registry


def create_app(settings: Settings | None = None, *, engine: Engine | None = None, registry: TaskRegistry | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configured = settings or Settings.from_env()
        handlers = registry
        if handlers is None:
            if configured.registry_path is None:
                raise ValueError("PYTASK_REGISTRY is required for the API")
            handlers = load_registry(configured.registry_path)
        database = engine if engine is not None else build_engine(configured)
        app.state.resources = APIResources(database, handlers)
        try:
            yield
        finally:
            del app.state.resources
            if engine is None:
                database.dispose()

    app = FastAPI(title="PyTask API", version="1.0.0", lifespan=lifespan)
    register_errors(app)
    return app
