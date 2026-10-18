import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine

pytestmark = pytest.mark.integration


def test_readiness_checks_the_existing_task_schema(database_client: TestClient) -> None:
    assert database_client.get("/health/ready").json() == {"status": "ok"}


def test_readiness_fails_when_schema_is_incomplete(database_client: TestClient, isolated_engine: Engine) -> None:
    with isolated_engine.begin() as connection:
        connection.execute(text("ALTER TABLE task_attempts RENAME TO hidden_attempts"))
    response = database_client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "database_unavailable"
    assert database_client.get("/health/live").status_code == 200
