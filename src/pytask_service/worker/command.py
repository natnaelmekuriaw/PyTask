import json
import sys
from threading import Event

from pytask_service.config import Settings
from pytask_service.db.engine import build_engine
from pytask_service.db.models import TaskStatus
from pytask_service.worker.loop import WorkerLoop
from pytask_service.worker.service import WorkedTask, Worker
from pytask_service.worker.signals import stop_on_signals


def run_one(settings: Settings) -> int:
    if settings.registry_path is None:
        raise ValueError("PYTASK_REGISTRY is required for workers")

    engine = build_engine(settings)
    try:
        worker = Worker(engine, settings.registry_path)
        with stop_on_signals(Event()):
            worked = worker.run_once()
        if worked is None:
            print("No pending tasks")
            return 0
        report(worked)
        return 0
    finally:
        engine.dispose()


def run_forever(settings: Settings, poll_interval: float) -> int:
    if settings.registry_path is None:
        raise ValueError("PYTASK_REGISTRY is required for workers")

    engine = build_engine(settings)
    try:
        worker = Worker(engine, settings.registry_path)
        stop_event = Event()
        loop = WorkerLoop(
            worker,
            poll_interval=poll_interval,
            stop_event=stop_event,
            on_result=report,
        )
        print(f"Worker {worker.worker_id} started", file=sys.stderr, flush=True)
        with stop_on_signals(stop_event):
            loop.run()
        print(f"Worker {worker.worker_id} stopped", file=sys.stderr, flush=True)
        return 0
    finally:
        engine.dispose()


def report(worked: WorkedTask) -> None:
    status = TaskStatus.SUCCEEDED if worked.outcome.succeeded else TaskStatus.FAILED
    print(json.dumps({"id": str(worked.id), "status": status.value}), flush=True)
