import pytest

from pytask_service.auth.issuance import IssuedKey
from pytask_service.auth.settings import AuthMode, AuthSettings


def test_explicit_disabled_mode_needs_no_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTASK_API_AUTH_MODE", "disabled")
    settings = AuthSettings.from_env()
    assert settings.mode is AuthMode.DISABLED
    assert settings.keys == ()
    assert settings.docs_enabled


def test_disabled_mode_rejects_an_accidentally_configured_manifest(
    key: IssuedKey,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTASK_API_AUTH_MODE", "disabled")
    monkeypatch.setenv("PYTASK_API_KEYS", key.manifest())
    with pytest.raises(ValueError, match="disabled"):
        AuthSettings.from_env()
