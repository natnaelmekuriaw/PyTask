from threading import Event
from uuid import uuid4

from pytask_service.worker.loop import WorkerLoop
from pytask_service.worker.outcome import TaskOutcome
from pytask_service.worker.service import WorkedTask


def test_loop_does_not_claim_after_stop_request() -> None:
    stop = Event()
    stop.set()

    class UnexpectedWorker:
        def run_once(self) -> None:
            raise AssertionError("No task should be claimed")

    loop = WorkerLoop(UnexpectedWorker(), stop_event=stop)

    assert loop.run() == 0


def test_loop_finishes_current_task_before_stopping() -> None:
    stop = Event()
    worked = WorkedTask(uuid4(), TaskOutcome.success(5))
    observed: list[WorkedTask] = []

    class ActiveWorker:
        def run_once(self) -> WorkedTask:
            stop.set()
            return worked

    loop = WorkerLoop(ActiveWorker(), stop_event=stop, on_result=observed.append)

    assert loop.run() == 1
    assert observed == [worked]
