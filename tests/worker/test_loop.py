from threading import Event
from uuid import uuid4

import pytest

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


def test_idle_loop_waits_between_claims() -> None:
    class StopAfterWait(Event):
        def __init__(self) -> None:
            super().__init__()
            self.timeouts: list[float] = []

        def wait(self, timeout: float | None = None) -> bool:
            assert timeout is not None
            self.timeouts.append(timeout)
            self.set()
            return True

    class IdleWorker:
        def run_once(self) -> None:
            return None

    stop = StopAfterWait()
    loop = WorkerLoop(IdleWorker(), poll_interval=0.25, stop_event=stop)

    assert loop.run() == 0
    assert stop.timeouts == [0.25]


@pytest.mark.parametrize("poll_interval", [0, -1, float("nan"), float("inf")])
def test_loop_rejects_invalid_poll_interval(poll_interval: float) -> None:
    with pytest.raises(ValueError, match="positive finite"):
        WorkerLoop(object(), poll_interval=poll_interval)
