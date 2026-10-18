from typing import cast

from pytask_service.json_value import InvalidJSONValue, normalize_json_value


class InvalidTaskArguments(ValueError):
    pass


def normalize_arguments(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise InvalidTaskArguments("Task arguments must be a JSON object")

    try:
        normalized = normalize_json_value(value, label="Task arguments")
    except InvalidJSONValue as exc:
        raise InvalidTaskArguments(str(exc)) from exc
    return cast(dict[str, object], normalized)
