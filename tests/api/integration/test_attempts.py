from collections.abc import Callable
from datetime import timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.clock import database_now
from pytask_service.db.models import Task
from pytask_service.worker.claim import claim_next
from pytask_service.worker.finish import finish_task
from pytask_service.worker.outcome import TaskOutcome

pytestmark = pytest.mark.integration


def test_existing_tasks_have_an_empty_attempt_page_before_execution(database_client: TestClient, submit: Callable[..., dict[str, Any]]) -> None:
    task = submit()
    response = database_client.get(f"/api/v1/tasks/{task['id']}/attempts")
    assert response.status_code == 200
    assert response.json() == {"items": [], "next_after": None}
