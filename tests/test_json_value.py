import math

import pytest

from pytask_service.json_value import InvalidJSONValue, normalize_json_value


@pytest.mark.parametrize("value", [None, "done", 42, [1, {"ok": True}]])
def test_result_accepts_any_json_value(value: object) -> None:
    assert normalize_json_value(value, label="Task result") == value


@pytest.mark.parametrize("value", [math.inf, {"bad": {1, 2}}, (1, 2)])
def test_result_rejects_non_json_values(value: object) -> None:
    with pytest.raises(InvalidJSONValue, match="Task result"):
        normalize_json_value(value, label="Task result")


def test_result_size_is_bounded() -> None:
    with pytest.raises(InvalidJSONValue, match="64 KiB"):
        normalize_json_value("x" * 65536, label="Task result")
