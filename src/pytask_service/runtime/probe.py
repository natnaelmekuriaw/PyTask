import json

from pytask_service.config import Settings
from pytask_service.db.engine import build_engine
from pytask_service.env_options import seconds_option
from pytask_service.runtime.http_probe import probe_api
from pytask_service.runtime.paths import RuntimePaths
from pytask_service.runtime.schema import check_schema


def run_probe(kind: str) -> int:
    if kind == "api":
        timeout = seconds_option(
            "PYTASK_PROBE_TIMEOUT_SECONDS", 3, minimum=0.1, maximum=5
        )
        probe_api(timeout)
    elif kind == "database":
        settings = Settings.from_env()
        paths = RuntimePaths.from_env()
        engine = build_engine(settings)
        try:
            check_schema(engine, paths)
        finally:
            engine.dispose()
    else:
        raise ValueError("Probe kind must be api or database")
    print(json.dumps({"status": "ok"}))
    return 0
