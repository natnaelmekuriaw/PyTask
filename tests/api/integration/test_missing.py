from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "resource",
    ["tasks/{id}", "tasks/{id}/attempts", "schedules/{id}", "schedules/{id}/tasks"],
)
def test_missing_resources_return_404(
    database_client: TestClient, resource: str
) -> None:
    response = database_client.get("/api/v1/" + resource.format(id=uuid4()))
    assert response.status_code == 404
    assert response.json()["error"]["code"].endswith("_not_found")


@pytest.mark.parametrize("action", ["pause", "resume"])
def test_missing_schedule_state_changes_return_404(
    database_client: TestClient, action: str
) -> None:
    response = database_client.post(f"/api/v1/schedules/{uuid4()}/{action}")
    assert response.status_code == 404
