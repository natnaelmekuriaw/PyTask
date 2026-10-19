import pytest

from pytask_service.auth.permissions import Permission
from tests.auth.conftest import ClientFactory


@pytest.mark.parametrize(
    ("permission", "method", "path"),
    [
        (Permission.TASKS_READ, "POST", "/api/v1/tasks"),
        (Permission.TASKS_SUBMIT, "GET", "/api/v1/tasks"),
        (Permission.TASKS_READ, "GET", "/api/v1/schedules"),
        (Permission.SCHEDULES_READ, "POST", "/api/v1/schedules"),
        (Permission.SCHEDULES_WRITE, "GET", "/api/v1/schedules"),
        (Permission.TASKS_READ, "GET", "/api/v1/monitoring"),
        (Permission.DOCS_READ, "POST", "/api/v1/tasks"),
    ],
)
def test_unrelated_permissions_are_denied_before_database_access(
    make_client: ClientFactory,
    permission: Permission,
    method: str,
    path: str,
) -> None:
    client, headers = make_client(frozenset({permission}))
    response = client.request(method, path, headers=headers, json={})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "insufficient_scope"
    assert 'error="insufficient_scope"' in response.headers["www-authenticate"]
