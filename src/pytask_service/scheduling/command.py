import json
import sys
from threading import Event

from pytask_service.config import Settings
from pytask_service.db.engine import build_engine
from pytask_service.scheduling.enqueue import ScheduledTask
from pytask_service.scheduling.loop import SchedulerLoop
from pytask_service.scheduling.policy import SchedulerPolicy
from pytask_service.scheduling.service import Scheduler
from pytask_service.worker.signals import stop_on_signals


def report(task: ScheduledTask) -> None:
    print(json.dumps({"id": str(task.id), "schedule_id": str(task.schedule_id), "scheduled_for": task.scheduled_for.isoformat(), "created": task.created}), flush=True)


def run_scheduler(settings: Settings, *, once: bool = False, policy: SchedulerPolicy | None = None) -> int:
    policy = policy or SchedulerPolicy()
    engine = build_engine(settings)
    try:
        scheduler = Scheduler(engine, policy)
        stopped = Event()
        with stop_on_signals(stopped):
            if once:
                tasks = scheduler.run_once()
                for task in tasks:
                    report(task)
                if not tasks:
                    print("No due schedules", file=sys.stderr)
            else:
                print("Scheduler started", file=sys.stderr, flush=True)
                SchedulerLoop(scheduler, policy=policy, stop_event=stopped, on_result=report).run()
                print("Scheduler stopped", file=sys.stderr, flush=True)
        return 0
    finally:
        engine.dispose()
