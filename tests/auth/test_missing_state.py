import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize("attribute", ["auth_settings", "auth_store"])
def test_unavailable_authentication_state_never_runs_handlers(
    client: TestClient, headers: dict[str, str], attribute: str,
) -> None:
    value = getattr(client.app.state, attribute)
    delattr(client.app.state, attribute)
    try:
        response = client.get("/api/v1/tasks", headers=headers)
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "authentication_unavailable"
    finally:
        setattr(client.app.state, attribute, value)

