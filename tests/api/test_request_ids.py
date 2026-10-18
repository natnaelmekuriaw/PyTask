from uuid import UUID

from fastapi.testclient import TestClient


def test_server_replaces_untrusted_request_identifiers(client: TestClient) -> None:
    first = client.get("/health/live", headers={"X-Request-ID": "untrusted"})
    second = client.get("/missing")
    assert first.status_code == 200 and second.status_code == 404
    ids = [response.headers["x-request-id"] for response in (first, second)]
    assert ids[0] != ids[1]
    assert all(UUID(identifier).version == 4 for identifier in ids)
    assert "untrusted" not in ids
