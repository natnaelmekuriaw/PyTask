import pytest

from pytask_service.auth.issuance import IssuedKey
from pytask_service.auth.settings import AuthMode, AuthSettings


def test_missing_manifest_cannot_start_required_authentication() -> None:
    with pytest.raises(ValueError, match="PYTASK_API_KEYS"):
        AuthSettings.from_env()


def test_required_mode_loads_only_digest_configuration(
    key: IssuedKey,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTASK_API_KEYS", key.manifest())
    settings = AuthSettings.from_env()
    assert settings.mode is AuthMode.REQUIRED
    assert settings.keys == (key.credential,)
    assert not settings.docs_enabled
    assert key.token not in repr(settings)
