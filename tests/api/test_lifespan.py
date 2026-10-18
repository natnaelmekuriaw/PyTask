import pytest
from fastapi.testclient import TestClient

from pytask_service.api import app as application
from pytask_service.config import Settings
from pytask_service.registry import TaskRegistry


class RecordingEngine:
    disposed = False

    def dispose(self) -> None:
        self.disposed = True


def test_import_and_factory_do_not_require_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYTASK_DATABASE_URL", raising=False)
    app = application.create_app()
    assert app.title == "PyTask API"


def test_lifespan_closes_only_the_engine_it_owns(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings("postgresql+psycopg://u:p@localhost/db")
    owned = RecordingEngine()
    monkeypatch.setattr(application, "build_engine", lambda settings: owned)
    with TestClient(application.create_app(settings, registry=TaskRegistry())):
        assert not owned.disposed
    assert owned.disposed
    borrowed = RecordingEngine()
    app = application.create_app(settings, engine=borrowed, registry=TaskRegistry())
    with TestClient(app):
        assert app.state.resources.engine is borrowed
    assert not borrowed.disposed
    assert not hasattr(app.state, "resources")


def test_missing_registry_fails_before_creating_an_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected(settings: Settings) -> None:
        raise AssertionError("engine must not be created")
    monkeypatch.setattr(application, "build_engine", unexpected)
    app = application.create_app(Settings("postgresql+psycopg://u:p@localhost/db"))
    with pytest.raises(ValueError, match="PYTASK_REGISTRY"):
        with TestClient(app):
            pass
