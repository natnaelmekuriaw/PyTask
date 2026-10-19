from pathlib import Path

import pytest

from pytask_service.config import Settings


def test_settings_read_the_url_file_without_adding_it_to_repr(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    url = "postgresql+psycopg://u:private-password@postgres/db"
    path = tmp_path / "url"
    path.write_text(url, encoding="utf-8")
    monkeypatch.delenv("PYTASK_DATABASE_URL", raising=False)
    monkeypatch.setenv("PYTASK_DATABASE_URL_FILE", str(path))
    settings = Settings.from_env()
    assert settings.database_url == url
    assert "private-password" not in repr(settings)


def test_invalid_file_content_does_not_appear_in_settings_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "url"
    path.write_bytes(b"private\x00url")
    monkeypatch.delenv("PYTASK_DATABASE_URL", raising=False)
    monkeypatch.setenv("PYTASK_DATABASE_URL_FILE", str(path))
    with pytest.raises(ValueError) as failure:
        Settings.from_env()
    assert "private" not in str(failure.value)
