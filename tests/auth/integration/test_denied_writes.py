import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.auth.permissions import Permission
from pytask_service.db.models import Task
from tests.auth.conftest import ClientFactory

pytestmark = pytest.mark.integration


def test_reader_and_anonymous_requests_cannot_enqueue(
    make_client: ClientFactory, isolated_engine: Engine,
) -> None:
    client, headers = make_client(frozenset({Permission.TASKS_READ}))
    payload = {"name": "math.add", "arguments": {"left": 1, "right": 2}}
    assert client.post("/api/v1/tasks", headers=headers, json=payload).status_code == 403
    assert client.post("/api/v1/tasks", json=payload).status_code == 401
    with Session(isolated_engine) as session:
        assert session.scalar(select(func.count()).select_from(Task)) == 0

