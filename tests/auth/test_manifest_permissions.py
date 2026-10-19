import json

import pytest

from pytask_service.auth.issuance import IssuedKey
from pytask_service.auth.manifest import parse_manifest


@pytest.mark.parametrize("scopes", [[], ["*"], ["admin"], ["tasks:read", "tasks:read"], [1], "tasks:read", None])
def test_permissions_must_be_explicit_supported_unique_names(
    key: IssuedKey, scopes: object,
) -> None:
    data = json.loads(key.manifest())
    data["keys"][0]["scopes"] = scopes
    with pytest.raises(ValueError):
        parse_manifest(json.dumps(data))

