from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "math.add", "max_attempts": "3"},
        {"name": "math.add", "run_at": "2027-01-01"},
        {"name": "math.add", "unknown": 1},
    ],
)
def test_invalid_submissions_fail_before_database_access(
    client: TestClient, payload: dict[str, object]
) -> None:
    response = client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "invalid_request" and error["details"]
    assert all("input" not in detail for detail in error["details"])


def test_malformed_json_has_a_consistent_bad_request_error(client: TestClient) -> None:
    response = client.post(
        "/api/v1/tasks", content="{", headers={"content-type": "application/json"}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_json"


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/tasks?limit=0",
        "/api/v1/tasks?status=unknown",
        "/api/v1/schedules?limit=101",
        "/api/v1/tasks/not-a-uuid",
        "/api/v1/schedules/not-a-uuid",
    ],
)
def test_invalid_collection_parameters_never_query_the_database(
    client: TestClient, path: str
) -> None:
    assert client.get(path).status_code == 422


def test_invalid_cursor_is_reported_without_running_a_query(client: TestClient) -> None:
    response = client.get("/api/v1/tasks?cursor=bad.cursor")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_cursor"


def test_oversized_and_non_json_requests_use_the_error_contract(
    client: TestClient,
) -> None:
    assert (
        client.post(
            "/api/v1/tasks",
            content=b"x" * (128 * 1024 + 1),
            headers={"content-type": "application/json"},
        ).status_code
        == 413
    )
    assert (
        client.post(
            "/api/v1/tasks", content="{}", headers={"content-type": "text/plain"}
        ).status_code
        == 415
    )


def test_nonfinite_invalid_input_still_produces_valid_error_json(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/tasks",
        content='{"name":"math.add","arguments":{"value":NaN}}',
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422
    assert "input" not in response.json()["error"]["details"][0]


def test_deep_arguments_are_rejected_before_database_access(client: TestClient) -> None:
    body = (
        b'{"name":"math.add","arguments":{"nested":'
        + b"[" * 40
        + b"0"
        + b"]" * 40
        + b"}}"
    )
    response = client.post(
        "/api/v1/tasks", content=body, headers={"content-type": "application/json"}
    )
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "invalid_request"
    assert "nested too deeply" in error["details"][0]["message"]


@pytest.mark.parametrize("action", ["pause", "resume"])
@pytest.mark.parametrize(
    "body,status", [(b'{"cancel_pending":true}', 422), (b"{", 400)]
)
def test_schedule_controls_validate_bodies_before_changing_state(
    client: TestClient, action: str, body: bytes, status: int
) -> None:
    response = client.post(
        f"/api/v1/schedules/{uuid4()}/{action}",
        content=body,
        headers={"content-type": "application/json"},
    )
    assert response.status_code == status
