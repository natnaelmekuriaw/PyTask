import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize("path", ["/openapi.json", "/unknown", "/api/v1/tasks/not-a-uuid"])
def test_authorized_responses_disable_storage_and_vary_on_authorization(
    client: TestClient, headers: dict[str, str], path: str,
) -> None:
    response = client.get(path, headers=headers)
    assert response.status_code in {200, 404, 422}
    assert response.headers["cache-control"] == "no-store"
    assert "authorization" in response.headers["vary"].lower()


def test_rejected_requests_have_unique_correlation_ids(client: TestClient) -> None:
    first, second = client.get("/api/v1/tasks"), client.get("/api/v1/tasks")
    assert len(first.headers["x-request-id"]) == 32
    assert first.headers["x-request-id"] != second.headers["x-request-id"]

