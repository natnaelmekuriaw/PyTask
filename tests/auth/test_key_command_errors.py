from pathlib import Path

import pytest

from pytask_service.auth.command import main


@pytest.mark.parametrize(
    "extra",
    [
        ["--id", "../unsafe", "--scope", "tasks:read"],
        ["--id", "reader", "--scope", "tasks:read", "--scope", "tasks:read"],
    ],
)
def test_invalid_issuance_does_not_create_files(
    tmp_path: Path,
    extra: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    token, manifest = tmp_path / "token", tmp_path / "manifest"
    assert (
        main(
            [
                "generate",
                *extra,
                "--token-file",
                str(token),
                "--manifest",
                str(manifest),
            ]
        )
        == 1
    )
    assert not token.exists()
    assert not manifest.exists()
    assert "Key command failed" in capsys.readouterr().err


def test_manifest_inspection_reports_safe_file_errors(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["inspect", "--manifest", "missing-private-path.json"]) == 1
    assert "missing-private-path" not in capsys.readouterr().err
