from threading import Event

import pytest

from pytask_service.worker.errors import LostClaimError
from pytask_service.worker.heartbeat import LeaseKeeper


def test_heartbeat_renews_while_task_runs() -> None:
    renewed = Event()

    def renew() -> bool:
        renewed.set()
        return True

    with LeaseKeeper(renew, 0.01) as keeper:
        assert renewed.wait(2)
        keeper.raise_if_lost()
        assert not keeper.cancel_event.is_set()


def test_rejected_renewal_cancels_execution() -> None:
    with LeaseKeeper(lambda: False, 0.01) as keeper:
        assert keeper.cancel_event.wait(2)
        with pytest.raises(LostClaimError):
            keeper.raise_if_lost()


def test_database_error_cancels_execution_with_its_cause() -> None:
    def unavailable() -> bool:
        raise OSError("database unavailable")

    with LeaseKeeper(unavailable, 0.01) as keeper:
        assert keeper.cancel_event.wait(2)
        with pytest.raises(LostClaimError) as raised:
            keeper.raise_if_lost()
        assert isinstance(raised.value.__cause__, OSError)


def test_stalled_renewal_is_cancelled_by_independent_watchdog() -> None:
    entered = Event()
    release = Event()

    def stalled() -> bool:
        entered.set()
        release.wait(2)
        return True

    with LeaseKeeper(stalled, 0.01, lease_seconds=0.15) as keeper:
        try:
            assert entered.wait(1)
            assert keeper.cancel_event.wait(1)
        finally:
            release.set()
        with pytest.raises(LostClaimError):
            keeper.raise_if_lost()
    assert keeper.cancel_event.is_set()
