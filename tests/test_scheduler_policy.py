import pytest

from pytask_service.scheduling.policy import SchedulerPolicy


@pytest.mark.parametrize("batch_size", [0, -1, True, 1001, 1.5])
def test_scheduler_rejects_invalid_batch_sizes(batch_size: int) -> None:
    with pytest.raises(ValueError, match="Batch size"):
        SchedulerPolicy(batch_size=batch_size)


@pytest.mark.parametrize("interval", [0, -1, float("nan"), float("inf")])
def test_scheduler_rejects_invalid_polling(interval: float) -> None:
    with pytest.raises(ValueError, match="Poll interval"):
        SchedulerPolicy(poll_interval=interval)


def test_scheduler_accepts_batch_boundaries() -> None:
    assert SchedulerPolicy(batch_size=1).batch_size == 1
    assert SchedulerPolicy(batch_size=1000).batch_size == 1000
