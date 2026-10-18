import pytest

from pytask_service.worker.policy import WorkerPolicy


@pytest.mark.parametrize("lease", [0, -1, float("inf"), float("nan")])
def test_lease_duration_must_be_finite_and_positive(lease: float) -> None:
    with pytest.raises(ValueError, match="lease_seconds"):
        WorkerPolicy(lease_seconds=lease)


def test_heartbeat_needs_room_before_lease_expiry() -> None:
    with pytest.raises(ValueError, match="one third"):
        WorkerPolicy(lease_seconds=30, heartbeat_seconds=20)


@pytest.mark.parametrize("size", [0, -1, 1001, True])
def test_recovery_batches_are_bounded(size: int) -> None:
    with pytest.raises(ValueError, match="recovery_batch_size"):
        WorkerPolicy(recovery_batch_size=size)
