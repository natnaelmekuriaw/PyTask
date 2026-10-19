from pathlib import Path

import pytest

from pytask_service.auth.settings import AuthSettings


@pytest.mark.parametrize("content", [b"", b"\xff", b"x" * 8193, b"not-json-secret"])
def test_invalid_manifest_files_fail_safely(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, content: bytes,
) -> None:
    manifest = tmp_path / "private-manifest.json"
    manifest.write_bytes(content)
    monkeypatch.setenv("PYTASK_API_KEYS_FILE", str(manifest))
    with pytest.raises(ValueError) as error:
        AuthSettings.from_env()
    assert str(manifest) not in str(error.value)
    assert "not-json-secret" not in str(error.value)


def test_missing_manifest_file_is_not_treated_as_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTASK_API_KEYS_FILE", str(tmp_path / "missing"))
    with pytest.raises(ValueError, match="PYTASK_API_KEYS_FILE"):
        AuthSettings.from_env()

