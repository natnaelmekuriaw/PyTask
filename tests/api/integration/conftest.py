from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine

from pytask_service.api.app import create_app
from pytask_service.config import Settings
from pytask_service.example_tasks import registry
from tests.worker.conftest import isolated_engine as isolated_engine


@pytest.fixture
def database_client(isolated_engine: Engine) -> Iterator[TestClient]:
    app = create_app(Settings("postgresql+psycopg://u:p@localhost/db"), engine=isolated_engine, registry=registry)
    with TestClient(app) as client:
        yield client


@pytest.fixture
def submit(database_client: TestClient) -> Callable[..., dict[str, Any]]:
    def create(**overrides: object) -> dict[str, Any]:
        response = database_client.post("/api/v1/tasks", json={"name": "math.add", "arguments": {"left": 1, "right": 2}, **overrides})
        assert response.status_code == 201, response.text
        return response.json()
    return create
