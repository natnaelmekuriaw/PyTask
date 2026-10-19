from fastapi.testclient import TestClient

from pytask_service.api.app import create_app
from pytask_service.auth.issuance import IssuedKey
from pytask_service.auth.settings import AuthSettings
from pytask_service.config import Settings
from pytask_service.example_tasks import registry
from tests.api.test_lifespan import RecordingEngine


def test_shutdown_removes_credentials_without_disposing_a_borrowed_engine(
    key: IssuedKey,
) -> None:
    engine = RecordingEngine()
    app = create_app(
        Settings("postgresql+psycopg://u:p@localhost/db"),
        engine=engine,
        registry=registry,
        auth=AuthSettings(keys=(key.credential,)),
    )
    with TestClient(app):
        assert hasattr(app.state, "auth_store")
    assert not hasattr(app.state, "auth_store")
    assert not hasattr(app.state, "auth_settings")
    assert not engine.disposed
