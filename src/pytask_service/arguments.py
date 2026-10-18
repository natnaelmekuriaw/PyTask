import json
import math
from typing import cast


MAX_ARGUMENT_BYTES = 64 * 1024
MAX_ARGUMENT_DEPTH = 32


class InvalidTaskArguments(ValueError):
    pass


def normalize_arguments(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise InvalidTaskArguments("Task arguments must be a JSON object")

    _validate_json(value, depth=0, active=set())
    try:
        encoded = json.dumps(value, allow_nan=False, separators=(",", ":"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise InvalidTaskArguments("Task arguments are not valid JSON") from exc

    if len(encoded.encode("utf-8")) > MAX_ARGUMENT_BYTES:
        raise InvalidTaskArguments("Task arguments exceed 64 KiB")
    return cast(dict[str, object], json.loads(encoded))


def _validate_json(value: object, depth: int, active: set[int]) -> None:
    if depth > MAX_ARGUMENT_DEPTH:
        raise InvalidTaskArguments("Task arguments are nested too deeply")
    if value is None or isinstance(value, (str, int, bool)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise InvalidTaskArguments("Task arguments must contain finite numbers")
        return
    if not isinstance(value, (dict, list)):
        raise InvalidTaskArguments("Task arguments must contain only JSON values")

    identity = id(value)
    if identity in active:
        raise InvalidTaskArguments("Task arguments contain a cycle")

    active.add(identity)
    try:
        if isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str):
                    raise InvalidTaskArguments("Task argument keys must be strings")
                _validate_json(item, depth + 1, active)
        else:
            for item in value:
                _validate_json(item, depth + 1, active)
    finally:
        active.remove(identity)
