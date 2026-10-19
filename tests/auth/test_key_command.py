from pathlib import Path

import pytest

from pytask_service.auth.command import main
from pytask_service.auth.files import read_manifest_file
from pytask_service.auth.store import KeyStore


def test_generate_command_writes_usable_keys_without_printing_them(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PYTASK_DATABASE_URL", raising=False)
    token, manifest = tmp_path / "token", tmp_path / "manifest"
    assert (
        main(
            [
                "generate",
                "--id",
                "reader",
                "--scope",
                "tasks:read",
                "--token-file",
                str(token),
                "--manifest",
                str(manifest),
            ]
        )
        == 0
    )
    value = token.read_text(encoding="utf-8").strip()
    assert KeyStore(read_manifest_file(manifest)).authenticate(value).key_id == "reader"
    captured = capsys.readouterr()
    assert value not in captured.out + captured.err
