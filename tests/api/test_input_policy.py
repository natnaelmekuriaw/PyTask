import pytest
from pydantic import ValidationError

from pytask_service.api.schemas.tasks import TaskSubmit


@pytest.mark.parametrize(
    "policy",
    [
        {"max_attempts": True},
        {"max_attempts": "3"},
        {"timeout_seconds": "10"},
        {"retry_max_seconds": float("inf")},
        {"timeout_seconds": 1e100},
        {"retry_base_seconds": 10, "retry_max_seconds": 1},
    ],
)
def test_http_policy_rejects_coercion_and_unsafe_durations(
    policy: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        TaskSubmit.model_validate({"name": "math.add", **policy})


def test_http_policy_keeps_the_engine_defaults() -> None:
    request = TaskSubmit(name="math.add")
    assert request.as_policy().max_attempts == 3
    assert request.as_policy().timeout_seconds == 300
