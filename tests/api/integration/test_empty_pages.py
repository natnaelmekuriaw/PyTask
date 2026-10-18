from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_empty_collections_have_no_continuation_cursor(database_client: TestClient) -> None:
    for path in ("/api/v1/tasks", "/api/v1/schedules"):
        assert database_client.get(path).json() == {"items": [], "next_cursor": None}


def test_filters_with_no_matches_return_an_empty_page(database_client: TestClient, submit: Callable[..., dict[str, Any]]) -> None:
    submit()
    response = database_client.get("/api/v1/tasks", params={"status": "failed"})
    assert response.status_code == 200 and response.json()["items"] == []
