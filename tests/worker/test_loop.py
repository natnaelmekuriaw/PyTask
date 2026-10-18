from threading import Event

from pytask_service.worker.loop import WorkerLoop


def test_loop_does_not_claim_after_stop_request() -> None:
    stop = Event()
    stop.set()

    class UnexpectedWorker:
        def run_once(self) -> None:
            raise AssertionError("No task should be claimed")

    loop = WorkerLoop(UnexpectedWorker(), stop_event=stop)

    assert loop.run() == 0
