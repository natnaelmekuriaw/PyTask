import hashlib

import pytest

from pytask_service.benchmarks import workloads


def test_noop_returns_its_input():
    assert workloads.noop(17) == 17


def test_sleep_uses_milliseconds_without_waiting(monkeypatch):
    calls = []
    monkeypatch.setattr(workloads, "sleep", calls.append)
    assert workloads.wait(5, 20) == 5
    assert calls == [0.02]


def test_checksum_matches_independent_sha256_steps():
    first = hashlib.sha256(b"7").digest()
    expected = hashlib.sha256(first).hexdigest()
    assert workloads.checksum(7, 2) == expected


@pytest.mark.parametrize(
    "function,args",
    [
        (workloads.wait, (1, -1)),
        (workloads.wait, (1, 1001)),
        (workloads.checksum, (1, 0)),
        (workloads.checksum, (1, 1000001)),
    ],
)
def test_handler_bounds_are_enforced(function, args):
    with pytest.raises(ValueError):
        function(*args)
