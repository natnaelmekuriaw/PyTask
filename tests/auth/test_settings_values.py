import pytest

from pytask_service.auth.settings import AuthSettings


@pytest.mark.parametrize("mode", ["", "off", "true", "REQUIRED", "unexpected-secret"])
def test_unknown_authentication_modes_fail_safely(
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    monkeypatch.setenv("PYTASK_API_AUTH_MODE", mode)
    with pytest.raises(ValueError, match="PYTASK_API_AUTH_MODE") as error:
        AuthSettings.from_env()
    assert "unexpected-secret" not in str(error.value)


@pytest.mark.parametrize("flag", ["", "1", "yes", "FALSE", "unexpected-secret"])
def test_documentation_flag_is_strict(
    monkeypatch: pytest.MonkeyPatch, flag: str
) -> None:
    monkeypatch.setenv("PYTASK_API_AUTH_MODE", "disabled")
    monkeypatch.setenv("PYTASK_API_DOCS_ENABLED", flag)
    with pytest.raises(ValueError, match="PYTASK_API_DOCS_ENABLED"):
        AuthSettings.from_env()
