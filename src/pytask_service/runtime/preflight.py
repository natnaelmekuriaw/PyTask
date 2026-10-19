from pytask_service.auth.settings import AuthSettings
from pytask_service.config import Settings
from pytask_service.db.engine import build_engine
from pytask_service.registry import load_registry
from pytask_service.runtime.paths import RuntimePaths
from pytask_service.runtime.roles import Role
from pytask_service.runtime.schema import check_schema


def prepare_service(role: Role, settings: Settings, paths: RuntimePaths) -> None:
    if role is Role.API:
        AuthSettings.from_env()
    if role in {Role.API, Role.WORKER}:
        if settings.registry_path is None:
            raise ValueError("PYTASK_REGISTRY is required for API and worker services")
        try:
            load_registry(settings.registry_path)
        except TypeError:
            raise ValueError("PYTASK_REGISTRY must refer to a TaskRegistry") from None
    engine = build_engine(settings)
    try:
        check_schema(engine, paths)
    finally:
        engine.dispose()
