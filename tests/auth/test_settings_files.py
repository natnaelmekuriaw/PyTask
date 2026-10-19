from pathlib import Path

import pytest

from pytask_service.auth.issuance import IssuedKey
from pytask_service.auth.settings import AuthSettings


def test_utf8_bom_manifest_files_work_on_windows(
    tmp_path: Path, key: IssuedKey, monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = tmp_path / "keys.json"
    manifest.write_text(key.manifest(), encoding="utf-8-sig")
    monkeypatch.setenv("PYTASK_API_KEYS_FILE", str(manifest))
    assert AuthSettings.from_env().keys == (key.credential,)


def test_manifest_sources_cannot_silently_override_each_other(
    key: IssuedKey, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTASK_API_KEYS", key.manifest())
    monkeypatch.setenv("PYTASK_API_KEYS_FILE", "private-path")
    with pytest.raises(ValueError, match="Set only one") as error:
        AuthSettings.from_env()
    assert "private-path" not in str(error.value)

