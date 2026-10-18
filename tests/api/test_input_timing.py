from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from pytask_service.api.schemas.tasks import TaskSubmit


@pytest.mark.parametrize(
    "timing",
    [
        {"run_at": "2027-01-01T12:00:00"},
        {"run_at": 123456},
        {"run_at": "2027-01-01T12:00:00Z", "delay_seconds": 0},
        {"delay_seconds": -1},
        {"delay_seconds": True},
    ],
)
def test_task_request_rejects_ambiguous_timing(timing: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        TaskSubmit.model_validate({"name": "math.add", **timing})


def test_task_request_normalizes_offsets_and_accepts_zero_delay() -> None:
    request = TaskSubmit.model_validate(
        {"name": "math.add", "run_at": "2027-01-01T12:00:00+03:00"}
    )
    assert request.run_at == datetime(2027, 1, 1, 9, tzinfo=UTC)
    assert TaskSubmit(name="math.add", delay_seconds=0).delay_seconds == 0
