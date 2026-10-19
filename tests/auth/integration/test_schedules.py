import pytest

from pytask_service.auth.permissions import Permission
from tests.auth.conftest import ClientFactory

pytestmark = pytest.mark.integration


def test_schedule_manager_can_control_dispatch_without_task_submission(make_client: ClientFactory) -> None:
    manager, headers = make_client(frozenset({Permission.SCHEDULES_WRITE}))
    response = manager.post("/api/v1/schedules", headers=headers, json={
        "name": "authenticated-report", "task_name": "math.add",
        "arguments": {"left": 1, "right": 2}, "interval_seconds": 60,
    })
    assert response.status_code == 201
    path = f'/api/v1/schedules/{response.json()["id"]}'
    assert manager.post(path + "/pause", headers=headers).json()["paused"] is True
    assert manager.post(path + "/resume", headers=headers).json()["paused"] is False
    observer, read_headers = make_client(frozenset({
        Permission.SCHEDULES_READ, Permission.TASKS_READ,
    }))
    assert observer.get(path, headers=read_headers).status_code == 200
    assert observer.get(path + "/tasks", headers=read_headers).status_code == 200
    assert observer.post(path + "/pause", headers=read_headers).status_code == 403

