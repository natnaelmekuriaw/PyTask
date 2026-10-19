import json
from pathlib import Path

import pytest

from pytask_service.auth.command import main
from pytask_service.auth.issuance import IssuedKey


def test_inspect_lists_only_key_ids_and_permissions(
    tmp_path: Path,
    key: IssuedKey,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "manifest.json"
    path.write_text(key.manifest(), encoding="utf-8")
    assert main(["inspect", "--manifest", str(path)]) == 0
    output = capsys.readouterr().out
    assert key.token not in output
    assert key.credential.sha256 not in output
    assert json.loads(output)["keys"][0]["id"] == "test"
