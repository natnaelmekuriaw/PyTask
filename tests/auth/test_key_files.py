from pathlib import Path

from pytask_service.auth.files import read_manifest_file, write_key_files
from pytask_service.auth.issuance import IssuedKey


def test_key_files_contain_separate_material(tmp_path: Path, key: IssuedKey) -> None:
    token, manifest = tmp_path / "token.txt", tmp_path / "keys.json"
    write_key_files(key, token, manifest)
    assert token.read_text(encoding="utf-8").strip() == key.token
    assert key.token not in manifest.read_text(encoding="utf-8")
    assert read_manifest_file(manifest) == (key.credential,)

