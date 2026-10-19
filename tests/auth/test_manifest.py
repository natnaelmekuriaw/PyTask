import json

from pytask_service.auth.issuance import IssuedKey
from pytask_service.auth.manifest import parse_manifest
from pytask_service.auth.permissions import ALL_PERMISSIONS
from pytask_service.auth.settings import AuthSettings


def test_issued_manifest_round_trips_without_usable_credentials(key: IssuedKey) -> None:
    parsed = parse_manifest(key.manifest())
    assert parsed == (key.credential,)
    assert parsed[0].permissions == ALL_PERMISSIONS
    assert key.token not in repr(AuthSettings(keys=parsed))


def test_manifest_contains_only_versioned_digest_records(key: IssuedKey) -> None:
    data = json.loads(key.manifest())
    assert set(data) == {"version", "keys"}
    assert set(data["keys"][0]) == {"id", "sha256", "scopes"}
