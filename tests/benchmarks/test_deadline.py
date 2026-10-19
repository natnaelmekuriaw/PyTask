import pytest

from pytask_service.benchmarks.deadline import Deadline


def test_deadline_uses_an_injected_monotonic_clock():
    now = [10.0]
    deadline = Deadline(5, clock=lambda: now[0])
    assert deadline.remaining == 5
    now[0] = 14.5
    deadline.check()
    assert deadline.remaining == 0.5
    now[0] = 15
    with pytest.raises(RuntimeError, match="deadline_exceeded"):
        deadline.check()
    now[0] = 99
    assert deadline.remaining == 0
