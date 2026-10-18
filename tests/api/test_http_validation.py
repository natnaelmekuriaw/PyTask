import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize("payload", [{"name": "math.add", "max_attempts": "3"}, {"name": "math.add", "run_at": "2027-01-01"}, {"name": "math.add", "unknown": 1}])
def test_invalid_submissions_fail_before_database_access(client: TestClient, payload: dict[str, object]) -> None:
    response = client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "invalid_request" and error["details"]
    assert all("input" not in detail for detail in error["details"])


def test_malformed_json_has_a_consistent_bad_request_error(client: TestClient) -> None:
    response = client.post("/api/v1/tasks", content="{", headers={"content-type": "application/json"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_json"


@pytest.mark.parametrize("path", ["/api/v1/tasks?limit=0", "/api/v1/tasks?status=unknown", "/api/v1/schedules?limit=101", "/api/v1/tasks/not-a-uuid", "/api/v1/schedules/not-a-uuid"])
def test_invalid_collection_parameters_never_query_the_database(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 422


def test_invalid_cursor_is_reported_without_running_a_query(client: TestClient) -> None:
    response = client.get("/api/v1/tasks?cursor=bad.cursor")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_cursor"
