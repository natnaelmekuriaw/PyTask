import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine

from pytask_service.api.app import create_app
from pytask_service.config import Settings
from pytask_service.example_tasks import registry

pytestmark = pytest.mark.integration


def test_creation_locations_include_the_proxy_root_path(isolated_engine: Engine) -> None:
    app = create_app(Settings("postgresql+psycopg://u:p@localhost/db"), engine=isolated_engine, registry=registry)
    with TestClient(app, root_path="/queue") as client:
        task = client.post("/api/v1/tasks", json={"name": "math.add", "arguments": {"left": 1, "right": 2}})
        schedule = client.post("/api/v1/schedules", json={"name": "report", "task_name": "math.add", "arguments": {"left": 1, "right": 2}, "interval_seconds": 60})
        assert task.status_code == schedule.status_code == 201
        for response in (task, schedule):
            assert response.headers["location"].startswith("/queue/api/v1/")
            assert client.get(response.headers["location"]).status_code == 200
