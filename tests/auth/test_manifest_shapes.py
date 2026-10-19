import json

import pytest

from pytask_service.auth.issuance import IssuedKey
from pytask_service.auth.manifest import parse_manifest


@pytest.mark.parametrize("data", [
    [], None, {}, {"version": True, "keys": []}, {"version": 2, "keys": []},
    {"version": 1, "keys": {}}, {"version": 1, "keys": []},
    {"version": 1, "keys": [], "extra": "secret"},
])
def test_invalid_manifest_shapes_fail_safely(data: object) -> None:
    with pytest.raises(ValueError, match="version 1 key manifest") as error:
        parse_manifest(json.dumps(data))
    assert "secret" not in str(error.value)


def test_unknown_credential_fields_are_rejected(key: IssuedKey) -> None:
    data = json.loads(key.manifest())
    data["keys"][0]["token"] = key.token
    with pytest.raises(ValueError) as error:
        parse_manifest(json.dumps(data))
    assert key.token not in str(error.value)

