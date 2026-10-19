import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(("method", "path"), [
    ("GET", "/api/v1/tasks"), ("POST", "/api/v1/tasks"),
    ("GET", "/api/v1/schedules"), ("POST", "/api/v1/schedules"),
    ("GET", "/api/v1/monitoring"), ("GET", "/openapi.json"),
    ("GET", "/unknown"), ("OPTIONS", "/api/v1/tasks"),
    ("HEAD", "/api/v1/tasks"), ("DELETE", "/api/v1/tasks"),
])
def test_missing_credentials_receive_a_bearer_challenge(
    client: TestClient, method: str, path: str,
) -> None:
    response = client.request(method, path)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == 'Bearer realm="pytask"'
    assert response.headers["cache-control"] == "no-store"
    if method != "HEAD":
        assert response.json()["error"]["code"] == "authentication_required"

