from fastapi import FastAPI
from fastapi.testclient import TestClient

from pytask_service.api.app import create_app
from pytask_service.auth.issuance import issue_key
from pytask_service.auth.permissions import Permission
from pytask_service.auth.settings import AuthSettings
from pytask_service.config import Settings
from pytask_service.example_tasks import registry
from tests.api.conftest import OfflineEngine


def test_mounting_does_not_bypass_documentation_permission() -> None:
    key = issue_key("reader", frozenset({Permission.TASKS_READ}))
    child = create_app(
        Settings("postgresql+psycopg://u:p@localhost/db"),
        engine=OfflineEngine(),
        registry=registry,
        auth=AuthSettings(keys=(key.credential,), docs_enabled=True),
    )
    parent = FastAPI()
    parent.mount("/queue", child)
    with TestClient(child), TestClient(parent) as client:
        assert client.get("/queue/health/live").status_code == 200
        response = client.get(
            "/queue/openapi.json",
            headers={
                "Authorization": f"Bearer {key.token}",
            },
        )
        assert response.status_code == 403
        assert client.get("/queue/api/v1/tasks").status_code == 401
