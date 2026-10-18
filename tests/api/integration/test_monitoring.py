from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine

from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


def test_api_reads_the_same_snapshot_as_database_clients(
    database_client: TestClient, isolated_engine: Engine,
) -> None:
    database = MonitoringDatabase(isolated_engine)
    database.task()
    database.task(available_at=database.now + timedelta(hours=1))
    response = database_client.get("/api/v1/monitoring")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["queue"]["total"] == 2
    assert body["queue"]["ready"] == body["queue"]["delayed"] == 1
    assert body["window_seconds"] == 3600
    assert body["attempts"]["execution"]["mean_seconds"] is None
    assert response.headers["cache-control"] == "no-store"
