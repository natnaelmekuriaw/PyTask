import logging

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.observability.events import log_event
from pytask_service.scheduling.dispatch import dispatch_due
from pytask_service.scheduling.enqueue import ScheduledTask
from pytask_service.scheduling.policy import SchedulerPolicy

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, engine: Engine, policy: SchedulerPolicy | None = None) -> None:
        self.engine = engine
        self.policy = policy or SchedulerPolicy()

    def run_once(self) -> list[ScheduledTask]:
        with Session(self.engine) as session, session.begin():
            tasks = dispatch_due(session, batch_size=self.policy.batch_size)
        for task in tasks:
            log_event(
                logger,
                "schedule.dispatched",
                task_id=task.id,
                schedule_id=task.schedule_id,
                scheduled_for=task.scheduled_for,
                created=task.created,
            )
        return tasks
