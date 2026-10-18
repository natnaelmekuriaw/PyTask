import pytest

from pytask_service.config import Settings


def test_settings_reads_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = "postgresql+psycopg://user:password@localhost:5432/pytask"
    monkeypatch.setenv("PYTASK_DATABASE_URL", database_url)

    assert Settings.from_env().database_url == database_url


@pytest.mark.parametrize(
    "database_url",
    ["", "   ", "not-a-url", "sqlite:///tasks.db", "postgresql://localhost"],
)
def test_settings_rejects_invalid_database_urls(
    monkeypatch: pytest.MonkeyPatch, database_url: str
) -> None:
    monkeypatch.setenv("PYTASK_DATABASE_URL", database_url)

    with pytest.raises(ValueError, match="PYTASK_DATABASE_URL"):
        Settings.from_env()
