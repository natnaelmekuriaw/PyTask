from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from pytask_service.api.app import create_app
from pytask_service.config import Settings
from pytask_service.example_tasks import registry


class OfflineEngine:
    def connect(self) -> None:
        raise AssertionError("Unit API checks must not connect to a database")


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(Settings("postgresql+psycopg://u:p@localhost/db"), engine=OfflineEngine(), registry=registry)
    with TestClient(app) as http:
        yield http
