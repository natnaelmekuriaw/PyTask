from pathlib import Path

import pytest

from pytask_service.auth.files import write_key_files
from pytask_service.auth.issuance import IssuedKey


@pytest.mark.parametrize("existing", ["token.txt", "keys.json"])
def test_existing_key_material_survives_generation_failure(
    tmp_path: Path, key: IssuedKey, existing: str,
) -> None:
    token, manifest = tmp_path / "token.txt", tmp_path / "keys.json"
    preserved = tmp_path / existing
    preserved.write_text("existing-private-value", encoding="utf-8")
    with pytest.raises(ValueError):
        write_key_files(key, token, manifest)
    assert preserved.read_text(encoding="utf-8") == "existing-private-value"
    assert not (manifest if preserved == token else token).exists()


def test_token_and_manifest_cannot_share_a_path(tmp_path: Path, key: IssuedKey) -> None:
    path = tmp_path / "both"
    with pytest.raises(ValueError, match="different paths"):
        write_key_files(key, path, path)
    assert not path.exists()

