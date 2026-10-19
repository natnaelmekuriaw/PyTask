import json

import pytest

from pytask_service.auth.issuance import IssuedKey
from pytask_service.auth.manifest import parse_manifest


def test_manifest_byte_limit_is_enforced(key: IssuedKey) -> None:
    with pytest.raises(ValueError):
        parse_manifest(key.manifest() + " " * 8193)


def test_excess_key_records_are_rejected_before_validation(key: IssuedKey) -> None:
    record = json.loads(key.manifest())["keys"][0]
    with pytest.raises(ValueError):
        parse_manifest(json.dumps({"version": 1, "keys": [record] * 33}))


def test_deeply_nested_json_produces_a_safe_configuration_error() -> None:
    with pytest.raises(ValueError, match="key manifest"):
        parse_manifest("[" * 1100 + "]" * 1100)

