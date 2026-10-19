import pytest

from pytask_service.runtime.worker_options import WorkerOptions


def test_heartbeat_cannot_exceed_a_third_of_the_lease(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTASK_WORKER_LEASE_SECONDS", "9")
    monkeypatch.setenv("PYTASK_WORKER_HEARTBEAT_SECONDS", "4")
    with pytest.raises(ValueError, match="one third"):
        WorkerOptions.from_env()


@pytest.mark.parametrize(
    "name,raw",
    [
        ("PYTASK_WORKER_POLL_SECONDS", "0"),
        ("PYTASK_WORKER_LEASE_SECONDS", "3601"),
        ("PYTASK_WORKER_HEARTBEAT_SECONDS", "nan"),
    ],
)
def test_invalid_worker_durations_fail_before_launch(
    monkeypatch: pytest.MonkeyPatch, name: str, raw: str
) -> None:
    monkeypatch.setenv(name, raw)
    with pytest.raises(ValueError, match=name):
        WorkerOptions.from_env()
