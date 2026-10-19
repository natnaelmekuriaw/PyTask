from pathlib import Path

import pytest

from pytask_service.auth import files
from pytask_service.auth.issuance import IssuedKey


def test_failed_manifest_write_rolls_back_new_token(
    tmp_path: Path,
    key: IssuedKey,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token, manifest = tmp_path / "token.txt", tmp_path / "keys.json"
    original = files._write_new

    def fail_manifest(path: Path, text: str) -> None:
        if path == manifest:
            raise OSError("private-filesystem-diagnostic")
        original(path, text)

    monkeypatch.setattr(files, "_write_new", fail_manifest)
    with pytest.raises(ValueError) as error:
        files.write_key_files(key, token, manifest)
    assert "private-filesystem-diagnostic" not in str(error.value)
    assert not token.exists()
    assert not manifest.exists()
