import json
import math


MAX_JSON_BYTES = 64 * 1024
MAX_JSON_DEPTH = 32


class InvalidJSONValue(ValueError):
    pass


def normalize_json_value(value: object, *, label: str) -> object:
    _validate_json(value, label=label, depth=0, active=set())
    try:
        encoded = json.dumps(value, allow_nan=False, separators=(",", ":"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise InvalidJSONValue(f"{label} is not valid JSON") from exc

    if len(encoded.encode("utf-8")) > MAX_JSON_BYTES:
        raise InvalidJSONValue(f"{label} exceeds 64 KiB")
    return json.loads(encoded)


def _validate_json(value: object, *, label: str, depth: int, active: set[int]) -> None:
    if depth > MAX_JSON_DEPTH:
        raise InvalidJSONValue(f"{label} is nested too deeply")
    if value is None or isinstance(value, (str, int, bool)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise InvalidJSONValue(f"{label} must contain finite numbers")
        return
    if not isinstance(value, (dict, list)):
        raise InvalidJSONValue(f"{label} must contain only JSON values")

    identity = id(value)
    if identity in active:
        raise InvalidJSONValue(f"{label} contains a cycle")

    active.add(identity)
    try:
        if isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str):
                    raise InvalidJSONValue(f"{label} keys must be strings")
                _validate_json(item, label=label, depth=depth + 1, active=active)
        else:
            for item in value:
                _validate_json(item, label=label, depth=depth + 1, active=active)
    finally:
        active.remove(identity)
