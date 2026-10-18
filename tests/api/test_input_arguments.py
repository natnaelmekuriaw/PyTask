import pytest
from pydantic import ValidationError

from pytask_service.api.schemas.tasks import TaskSubmit


@pytest.mark.parametrize(
    "arguments", [[], {"value": float("nan")}, {"value": "x" * 65536}]
)
def test_http_arguments_follow_the_engine_json_contract(arguments: object) -> None:
    with pytest.raises(ValidationError):
        TaskSubmit.model_validate({"name": "math.add", "arguments": arguments})


def test_submission_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError, match="extra"):
        TaskSubmit.model_validate({"name": "math.add", "retry_count": 5})


def test_arguments_are_copied_when_a_request_is_validated() -> None:
    arguments = {"nested": {"value": 1}}
    request = TaskSubmit(name="math.add", arguments=arguments)
    arguments["nested"]["value"] = 2
    assert request.arguments == {"nested": {"value": 1}}
