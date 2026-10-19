from pathlib import Path

import pytest

from pytask_service.environment import read_secret


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig"])
def test_secret_files_accept_utf8_and_optional_bom(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    encoding: str,
) -> None:
    path = tmp_path / "database-url.txt"
    path.write_text("postgresql+psycopg://u:p@postgres/db\n", encoding=encoding)
    monkeypatch.delenv("PYTASK_DATABASE_URL", raising=False)
    monkeypatch.setenv("PYTASK_DATABASE_URL_FILE", str(path))
    assert read_secret("PYTASK_DATABASE_URL") == "postgresql+psycopg://u:p@postgres/db"


def test_empty_direct_values_allow_a_secret_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "url"
    path.write_text("file-value", encoding="utf-8")
    monkeypatch.setenv("PYTASK_DATABASE_URL", "")
    monkeypatch.setenv("PYTASK_DATABASE_URL_FILE", str(path))
    assert read_secret("PYTASK_DATABASE_URL") == "file-value"
