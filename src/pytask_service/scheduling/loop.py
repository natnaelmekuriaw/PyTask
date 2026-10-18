from collections.abc import Callable
from threading import Event
from typing import Protocol

from pytask_service.scheduling.enqueue import ScheduledTask
from pytask_service.scheduling.policy import SchedulerPolicy


class TaskScheduler(Protocol):
    def run_once(self) -> list[ScheduledTask]: ...


class SchedulerLoop:
    def __init__(
        self,
        scheduler: TaskScheduler,
        *,
        policy: SchedulerPolicy | None = None,
        stop_event: Event | None = None,
        on_result: Callable[[ScheduledTask], None] | None = None,
    ) -> None:
        self.scheduler = scheduler
        self.policy = policy or SchedulerPolicy()
        self.stop_event = stop_event or Event()
        self.on_result = on_result

    def run(self) -> int:
        created = 0
        while not self.stop_event.is_set():
            tasks = self.scheduler.run_once()
            for task in tasks:
                created += int(task.created)
                if self.on_result is not None:
                    self.on_result(task)
            if len(tasks) < self.policy.batch_size:
                self.stop_event.wait(self.policy.poll_interval)
        return created
