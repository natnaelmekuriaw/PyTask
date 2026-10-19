import pytest

from pytask_service.auth.credentials import Credential
from pytask_service.auth.permissions import Permission
from pytask_service.auth.settings import AuthMode, AuthSettings


@pytest.mark.parametrize("digest", ["", "f" * 63, "G" * 64, "F" * 64, None])
def test_invalid_verification_digests_are_rejected(digest: str) -> None:
    with pytest.raises(ValueError, match="sha256"):
        Credential("reader", digest, frozenset({Permission.TASKS_READ}))


def test_permissions_and_settings_are_immutable_validated_values() -> None:
    with pytest.raises(ValueError, match="permissions"):
        Credential("reader", "f" * 64, frozenset())
    with pytest.raises(ValueError, match="permissions"):
        Credential("reader", "f" * 64, frozenset({"tasks:read"}))
    with pytest.raises(ValueError, match="settings"):
        AuthSettings(mode="disabled")
    with pytest.raises(ValueError, match="settings"):
        AuthSettings(mode=AuthMode.DISABLED, docs_enabled=1)

