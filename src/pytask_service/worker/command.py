import json
import logging
from threading import Event

from pytask_service.config import Settings
from pytask_service.db.engine import build_engine
from pytask_service.db.models import TaskStatus
from pytask_service.observability.events import log_event
from pytask_service.worker.loop import WorkerLoop
from pytask_service.worker.policy import WorkerPolicy
from pytask_service.worker.service import WorkedTask, Worker
from pytask_service.worker.signals import stop_on_signals

logger = logging.getLogger(__name__)


def run_one(settings: Settings, policy: WorkerPolicy | None = None) -> int:
    if settings.registry_path is None:
        raise ValueError("PYTASK_REGISTRY is required for workers")

    engine = build_engine(settings)
    try:
        worker = Worker(engine, settings.registry_path, policy=policy)
        with stop_on_signals(Event()):
            worked = worker.run_once()
        if worked is None:
            print("No pending tasks")
            return 0
        report(worked)
        return 0
    finally:
        engine.dispose()


def run_forever(
    settings: Settings, poll_interval: float, policy: WorkerPolicy | None = None
) -> int:
    if settings.registry_path is None:
        raise ValueError("PYTASK_REGISTRY is required for workers")

    engine = build_engine(settings)
    try:
        worker = Worker(engine, settings.registry_path, policy=policy)
        stop_event = Event()
        loop = WorkerLoop(
            worker,
            poll_interval=poll_interval,
            stop_event=stop_event,
            on_result=report,
        )
        log_event(logger, "worker.started", worker_id=worker.worker_id)
        with stop_on_signals(stop_event):
            loop.run()
        log_event(logger, "worker.stopped", worker_id=worker.worker_id)
        return 0
    finally:
        engine.dispose()


def report(worked: WorkedTask) -> None:
    status = worked.status or (
        TaskStatus.SUCCEEDED if worked.outcome.succeeded else TaskStatus.FAILED
    )
    print(
        json.dumps(
            {
                "id": str(worked.id),
                "status": status.value,
                "attempt": worked.attempt_number,
            }
        ),
        flush=True,
    )
