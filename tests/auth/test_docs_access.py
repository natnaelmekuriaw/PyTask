from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient


from pytask_service.auth.permissions import Permission


def test_schema_is_accessible_with_documentation_permission(make_client: Callable) -> None:
    client, headers = make_client(frozenset({Permission.DOCS_READ}))
    response = client.get("/openapi.json", headers=headers)
    assert response.status_code == 200
    assert "/api/v1/tasks" in response.json()["paths"]


def test_data_access_does_not_grant_documentation_access(make_client: Callable) -> None:
    client, headers = make_client(frozenset({Permission.TASKS_READ}))
    assert client.get("/openapi.json", headers=headers).status_code == 403


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/docs/oauth2-redirect"])
def test_interactive_docs_are_hidden_in_required_mode(
    client: TestClient, headers: dict[str, str], path: str,
) -> None:
    assert client.get(path, headers=headers).status_code == 404

