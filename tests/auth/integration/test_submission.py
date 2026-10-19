import pytest

from pytask_service.auth.permissions import Permission
from tests.auth.conftest import ClientFactory

pytestmark = pytest.mark.integration


def test_producer_can_submit_and_reader_can_inspect(make_client: ClientFactory) -> None:
    producer, producer_headers = make_client(frozenset({Permission.TASKS_SUBMIT}))
    response = producer.post("/api/v1/tasks", headers=producer_headers, json={
        "name": "math.add", "arguments": {"left": 1, "right": 2},
    })
    assert response.status_code == 201
    path = f'/api/v1/tasks/{response.json()["id"]}'
    assert producer.get(path, headers=producer_headers).status_code == 403
    reader, reader_headers = make_client(frozenset({Permission.TASKS_READ}))
    assert reader.get(path, headers=reader_headers).json()["status"] == "pending"
    assert reader.get(path + "/attempts", headers=reader_headers).status_code == 200

