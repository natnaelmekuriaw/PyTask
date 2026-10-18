from datetime import UTC, datetime
from threading import Event
from uuid import uuid4

from pytask_service.scheduling.enqueue import ScheduledTask
from pytask_service.scheduling.loop import SchedulerLoop
from pytask_service.scheduling.policy import SchedulerPolicy


def test_stopped_scheduler_does_not_claim_a_batch() -> None:
    class UnexpectedScheduler:
        def run_once(self) -> list[ScheduledTask]:
            raise AssertionError("should not dispatch")
    stopped = Event()
    stopped.set()
    assert SchedulerLoop(UnexpectedScheduler(), stop_event=stopped).run() == 0


def test_scheduler_reports_a_committed_batch_before_stopping() -> None:
    stopped = Event()
    task = ScheduledTask(uuid4(), uuid4(), datetime.now(UTC))
    class OneBatch:
        def run_once(self) -> list[ScheduledTask]:
            stopped.set()
            return [task]
    reports: list[ScheduledTask] = []
    loop = SchedulerLoop(OneBatch(), stop_event=stopped, on_result=reports.append)
    assert loop.run() == 1
    assert reports == [task]


def test_full_batches_drain_without_idle_waiting() -> None:
    stopped = Event()
    task = ScheduledTask(uuid4(), uuid4(), datetime.now(UTC), created=False)
    class TwoBatches:
        calls = 0
        def run_once(self) -> list[ScheduledTask]:
            self.calls += 1
            if self.calls == 2:
                stopped.set()
            return [task]
    scheduler = TwoBatches()
    loop = SchedulerLoop(scheduler, policy=SchedulerPolicy(batch_size=1, poll_interval=3600), stop_event=stopped)
    assert loop.run() == 0
    assert scheduler.calls == 2
