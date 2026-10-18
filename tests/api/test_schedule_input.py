import pytest
from pydantic import ValidationError

from pytask_service.api.schemas.schedules import ScheduleCreate


@pytest.mark.parametrize("changes", [
    {"name": "Upper"}, {"interval_seconds": True}, {"interval_seconds": 1.5},
    {"interval_seconds": 0}, {"paused": "false"}, {"start_at": "2027-01-01"},
])
def test_schedule_requests_reject_invalid_definitions(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ScheduleCreate.model_validate({"name": "report", "task_name": "math.add", "interval_seconds": 60, **changes})


def test_paused_schedule_keeps_its_explicit_start() -> None:
    request = ScheduleCreate.model_validate({"name": "report", "task_name": "math.add", "interval_seconds": 60, "paused": True, "start_at": "2027-01-01T00:00:00Z"})
    assert request.paused and request.start_at is not None


def test_schedule_start_must_allow_the_next_occurrence() -> None:
    with pytest.raises(ValidationError, match="timestamp range"):
        ScheduleCreate.model_validate({"name": "report", "task_name": "math.add", "interval_seconds": 60, "start_at": "9999-12-31T23:59:59Z"})
