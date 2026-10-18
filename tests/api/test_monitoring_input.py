import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize("window", ["0", "59", "604801", "true", "60.5", "private"])
def test_invalid_windows_do_not_open_database_connections(
    client: TestClient, window: str,
) -> None:
    response = client.get("/api/v1/monitoring", params={"window_seconds": window})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
