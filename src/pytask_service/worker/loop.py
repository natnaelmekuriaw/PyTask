from collections.abc import Callable
from threading import Event

from pytask_service.worker.service import WorkedTask, Worker


class WorkerLoop:
    def __init__(
        self,
        worker: Worker,
        *,
        poll_interval: float = 0.5,
        stop_event: Event | None = None,
        on_result: Callable[[WorkedTask], None] | None = None,
    ) -> None:
        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")
        self.worker = worker
        self.poll_interval = poll_interval
        self.stop_event = stop_event or Event()
        self.on_result = on_result

    def run(self) -> int:
        completed = 0
        while not self.stop_event.is_set():
            worked = self.worker.run_once()
            if worked is None:
                self.stop_event.wait(self.poll_interval)
                continue
            completed += 1
            if self.on_result is not None:
                self.on_result(worked)
        return completed
