import pytest

from pytask_service.auth.permissions import Permission
from tests.auth.conftest import ClientFactory


@pytest.mark.parametrize("action", ["pause", "resume"])
def test_schedule_readers_cannot_change_dispatch_state(make_client: ClientFactory, action: str) -> None:
    client, headers = make_client(frozenset({Permission.SCHEDULES_READ}))
    assert client.post(f"/api/v1/schedules/invalid/{action}", headers=headers).status_code == 403


@pytest.mark.parametrize("permission", [Permission.SCHEDULES_READ, Permission.TASKS_READ])
def test_schedule_history_requires_both_read_permissions(
    make_client: ClientFactory, permission: Permission,
) -> None:
    client, headers = make_client(frozenset({permission}))
    response = client.get("/api/v1/schedules/invalid/tasks", headers=headers)
    assert response.status_code == 403
    assert 'scope="schedules:read tasks:read"' in response.headers["www-authenticate"]


def test_combined_permissions_allow_occurrence_input_validation(make_client: ClientFactory) -> None:
    client, headers = make_client(frozenset({Permission.SCHEDULES_READ, Permission.TASKS_READ}))
    assert client.get("/api/v1/schedules/invalid/tasks", headers=headers).status_code == 422

