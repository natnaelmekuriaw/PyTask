import pytest

from pytask_service.auth.permissions import Permission
from tests.auth.conftest import ClientFactory


@pytest.mark.parametrize(
    ("permission", "method", "path"),
    [
        (Permission.TASKS_SUBMIT, "POST", "/api/v1/tasks"),
        (Permission.TASKS_READ, "GET", "/api/v1/tasks/not-a-uuid"),
        (Permission.SCHEDULES_WRITE, "POST", "/api/v1/schedules"),
        (Permission.SCHEDULES_READ, "GET", "/api/v1/schedules/not-a-uuid"),
        (Permission.MONITORING_READ, "GET", "/api/v1/monitoring?window_seconds=0"),
    ],
)
def test_correct_permission_preserves_existing_validation(
    make_client: ClientFactory,
    permission: Permission,
    method: str,
    path: str,
) -> None:
    client, headers = make_client(frozenset({permission}))
    response = client.request(method, path, headers=headers, json={})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
