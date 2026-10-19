import pytest
from fastapi.testclient import TestClient


def test_liveness_does_not_require_or_validate_a_key(client: TestClient) -> None:
    response = client.get("/health/live", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(("method", "path"), [
    ("GET", "/health/live/extra"), ("POST", "/health/live"),
    ("GET", "/health/ready/extra"), ("GET", "/health"),
    ("GET", "/health/live/"),
])
def test_health_exemptions_are_exact_get_paths(
    client: TestClient, method: str, path: str,
) -> None:
    assert client.request(method, path).status_code == 401

