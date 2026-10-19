import json

import pytest

from pytask_service.auth.issuance import IssuedKey
from pytask_service.auth.manifest import parse_manifest


def test_duplicate_json_fields_are_rejected(key: IssuedKey) -> None:
    text = key.manifest().replace('"version": 1', '"version": 1, "version": 1')
    with pytest.raises(ValueError):
        parse_manifest(text)


@pytest.mark.parametrize("field", ["id", "sha256"])
def test_duplicate_credential_identity_is_rejected(key: IssuedKey, field: str) -> None:
    data = json.loads(key.manifest())
    second = dict(data["keys"][0])
    second["id"] = "second"
    second["sha256"] = "f" * 64
    second[field] = data["keys"][0][field]
    data["keys"].append(second)
    with pytest.raises(ValueError):
        parse_manifest(json.dumps(data))

