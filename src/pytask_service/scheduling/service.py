from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.scheduling.dispatch import dispatch_due
from pytask_service.scheduling.enqueue import ScheduledTask
from pytask_service.scheduling.policy import SchedulerPolicy


class Scheduler:
    def __init__(self, engine: Engine, policy: SchedulerPolicy | None = None) -> None:
        self.engine = engine
        self.policy = policy or SchedulerPolicy()

    def run_once(self) -> list[ScheduledTask]:
        with Session(self.engine) as session, session.begin():
            tasks = dispatch_due(session, batch_size=self.policy.batch_size)
        return tasks
