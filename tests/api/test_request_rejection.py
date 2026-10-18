from fastapi.testclient import TestClient

from pytask_service.api.body_limit import MAX_REQUEST_BYTES


def test_body_limit_failures_are_correlated_before_routing(client: TestClient) -> None:
    response = client.post(
        "/api/v1/tasks",
        content=b"x" * (MAX_REQUEST_BYTES + 1),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
    assert len(response.headers["x-request-id"]) == 32
    invalid = client.post("/api/v1/tasks", content="not json")
    assert invalid.status_code == 415
    assert invalid.headers["x-request-id"] != response.headers["x-request-id"]
