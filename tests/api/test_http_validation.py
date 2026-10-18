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
