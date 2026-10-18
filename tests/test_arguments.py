import math

import pytest

from pytask_service.arguments import InvalidTaskArguments, normalize_arguments


def test_normalize_arguments_copies_nested_json() -> None:
    source = {"user": {"name": "Ada"}, "tags": ["urgent", None]}

    result = normalize_arguments(source)
    source["user"]["name"] = "Changed"

    assert result == {"user": {"name": "Ada"}, "tags": ["urgent", None]}


@pytest.mark.parametrize(
    "value",
    [[], {1: "value"}, {"value": (1, 2)}, {"value": math.nan}],
)
def test_rejects_non_json_arguments(value: object) -> None:
    with pytest.raises(InvalidTaskArguments):
        normalize_arguments(value)


def test_rejects_cyclic_arguments() -> None:
    values: list[object] = []
    values.append(values)

    with pytest.raises(InvalidTaskArguments, match="cycle"):
        normalize_arguments({"values": values})


def test_rejects_oversized_arguments() -> None:
    with pytest.raises(InvalidTaskArguments, match="64 KiB"):
        normalize_arguments({"text": "x" * 65536})
