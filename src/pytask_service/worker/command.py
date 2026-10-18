import json

from pytask_service.config import Settings
from pytask_service.db.engine import build_engine
from pytask_service.db.models import TaskStatus
from pytask_service.worker.service import WorkedTask, Worker


def run_one(settings: Settings) -> int:
    if settings.registry_path is None:
        raise ValueError("PYTASK_REGISTRY is required for workers")

    engine = build_engine(settings)
    try:
        worker = Worker(engine, settings.registry_path)
        worked = worker.run_once()
        if worked is None:
            print("No pending tasks")
            return 0
        report(worked)
        return 0
    finally:
        engine.dispose()


def report(worked: WorkedTask) -> None:
    status = TaskStatus.SUCCEEDED if worked.outcome.succeeded else TaskStatus.FAILED
    print(json.dumps({"id": str(worked.id), "status": status.value}), flush=True)
