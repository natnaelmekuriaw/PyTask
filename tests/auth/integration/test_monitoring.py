import pytest

from pytask_service.auth.permissions import Permission
from tests.auth.conftest import ClientFactory

pytestmark = pytest.mark.integration


def test_monitoring_permission_is_sufficient_only_for_statistics(make_client: ClientFactory) -> None:
    client, headers = make_client(frozenset({Permission.MONITORING_READ}))
    response = client.get("/api/v1/monitoring", headers=headers)
    assert response.status_code == 200
    assert response.json()["queue"]["total"] == 0
    assert client.get("/api/v1/tasks", headers=headers).status_code == 403
    assert client.get("/api/v1/schedules", headers=headers).status_code == 403

