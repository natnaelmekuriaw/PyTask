import multiprocessing
from time import monotonic
from uuid import uuid4

from pytask_service.worker.claim import ClaimedTask
from pytask_service.worker.runner import run_in_process


def test_timeout_stops_and_reaps_the_child() -> None:
    before = {child.pid for child in multiprocessing.active_children()}
    task = ClaimedTask(
        uuid4(), "test.sleep", {"seconds": 30}, "worker-one", timeout_seconds=0.3
    )
    started = monotonic()

    outcome = run_in_process("tests.worker.sample_tasks:registry", task)

    assert outcome.timed_out
    assert monotonic() - started < 8
    assert {child.pid for child in multiprocessing.active_children()} == before


def test_deadline_still_applies_after_result_is_sent() -> None:
    task = ClaimedTask(
        uuid4(), "test.linger", {}, "worker-one", timeout_seconds=0.5
    )

    outcome = run_in_process("tests.worker.sample_tasks:registry", task)

    assert outcome.timed_out
