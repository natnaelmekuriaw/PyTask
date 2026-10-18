import pytest

from pytask_service.policy import TaskPolicy


@pytest.mark.parametrize("attempts", [0, -1, 1001, True, 1.5])
def test_policy_rejects_invalid_attempt_limit(attempts: int) -> None:
    with pytest.raises(ValueError, match="max_attempts"):
        TaskPolicy(max_attempts=attempts)


@pytest.mark.parametrize("duration", [0, -1, float("nan"), float("inf")])
def test_policy_rejects_invalid_timeout(duration: float) -> None:
    with pytest.raises(ValueError, match="timeout_seconds"):
        TaskPolicy(timeout_seconds=duration)


def test_policy_rejects_inverted_backoff_bounds() -> None:
    with pytest.raises(ValueError, match="cannot exceed"):
        TaskPolicy(retry_base_seconds=10, retry_max_seconds=1)
