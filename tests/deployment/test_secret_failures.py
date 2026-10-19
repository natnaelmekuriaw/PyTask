from pathlib import Path

import pytest

from pytask_service.environment import MAX_SECRET_BYTES, read_secret


@pytest.mark.parametrize(
    "content", [b"", b" \r\n", b"\xff", b"x" * (MAX_SECRET_BYTES + 1)]
)
def test_invalid_secret_files_have_safe_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    content: bytes,
) -> None:
    path = tmp_path / "private-name"
    path.write_bytes(content)
    monkeypatch.delenv("PYTASK_DATABASE_URL", raising=False)
    monkeypatch.setenv("PYTASK_DATABASE_URL_FILE", str(path))
    with pytest.raises(ValueError) as failure:
        read_secret("PYTASK_DATABASE_URL")
    assert "PYTASK_DATABASE_URL_FILE" in str(failure.value)
    assert "private-name" not in str(failure.value)


def test_directories_and_missing_files_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("PYTASK_DATABASE_URL", raising=False)
    for path in (tmp_path, tmp_path / "missing"):
        monkeypatch.setenv("PYTASK_DATABASE_URL_FILE", str(path))
        with pytest.raises(ValueError, match="Cannot read"):
            read_secret("PYTASK_DATABASE_URL")
