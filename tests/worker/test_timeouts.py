import multiprocessing
from threading import Event, Timer
from time import monotonic
from uuid import uuid4

import pytest

from pytask_service.worker.claim import ClaimedTask
from pytask_service.worker.errors import LostClaimError
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
    task = ClaimedTask(uuid4(), "test.linger", {}, "worker-one", timeout_seconds=0.5)

    outcome = run_in_process("tests.worker.sample_tasks:registry", task)

    assert outcome.timed_out


def test_lost_lease_stops_running_child() -> None:
    before = {child.pid for child in multiprocessing.active_children()}
    task = ClaimedTask(uuid4(), "test.sleep", {"seconds": 30}, "worker-one")
    cancel = Event()
    timer = Timer(0.3, cancel.set)
    timer.start()
    try:
        with pytest.raises(LostClaimError):
            run_in_process("tests.worker.sample_tasks:registry", task, cancel)
    finally:
        timer.cancel()
        timer.join(timeout=1)
    assert {child.pid for child in multiprocessing.active_children()} == before


def test_pre_cancelled_claim_never_starts_a_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cancel = Event()
    cancel.set()
    task = ClaimedTask(uuid4(), "test.sleep", {"seconds": 30}, "worker-one")

    def unexpected_context(method: str) -> None:
        raise AssertionError("A cancelled claim must not start a process")

    monkeypatch.setattr(multiprocessing, "get_context", unexpected_context)
    with pytest.raises(LostClaimError):
        run_in_process("tests.worker.sample_tasks:registry", task, cancel)
