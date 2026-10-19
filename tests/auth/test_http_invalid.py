from fastapi.testclient import TestClient

from pytask_service.auth.issuance import IssuedKey, issue_key
from pytask_service.auth.permissions import ALL_PERMISSIONS


def test_unknown_and_incorrect_credentials_have_identical_responses(
    client: TestClient,
    key: IssuedKey,
) -> None:
    responses = [
        client.get(
            "/api/v1/tasks",
            headers={
                "Authorization": f"Bearer {issue_key(key_id, ALL_PERMISSIONS).token}"
            },
        )
        for key_id in ("test", "unknown")
    ]
    assert responses[0].json() == responses[1].json()
    assert responses[0].status_code == responses[1].status_code == 401
    assert 'error="invalid_token"' in responses[0].headers["www-authenticate"]


def test_duplicate_authorization_is_a_client_error(
    client: TestClient, key: IssuedKey
) -> None:
    response = client.get(
        "/api/v1/tasks",
        headers=[
            ("Authorization", f"Bearer {key.token}"),
            ("Authorization", f"Bearer {key.token}"),
        ],
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_request"
