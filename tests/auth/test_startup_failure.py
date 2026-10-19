import pytest
from fastapi.testclient import TestClient

from pytask_service.api import app as application
from pytask_service.config import Settings
from pytask_service.example_tasks import registry


def test_invalid_authentication_prevents_engine_creation(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected(settings: Settings) -> None:
        raise AssertionError("database engine created before credential validation")

    monkeypatch.setattr(application, "build_engine", unexpected)
    monkeypatch.setenv("PYTASK_API_KEYS", "private-invalid-manifest")
    app = application.create_app(
        Settings("postgresql+psycopg://u:p@localhost/db"), registry=registry,
    )
    with pytest.raises(ValueError, match="key manifest") as error:
        with TestClient(app):
            pass
    assert "private-invalid-manifest" not in str(error.value)
    assert not hasattr(app.state, "auth_store")

