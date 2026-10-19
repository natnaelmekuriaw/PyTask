import logging

from fastapi.testclient import TestClient

from pytask_service.auth.issuance import IssuedKey
from tests.observability.conftest import event_records as event_records


def test_authentication_logs_never_include_credential_material(
    client: TestClient,
    key: IssuedKey,
    headers: dict[str, str],
    event_records: list[logging.LogRecord],
) -> None:
    client.get("/api/v1/tasks", headers={"Authorization": "Bearer private-bad-token"})
    client.get("/openapi.json", headers=headers)
    fields = [record.event_fields for record in event_records]
    text = repr(fields)
    assert key.token not in text
    assert key.credential.sha256 not in text
    assert "private-bad-token" not in text
    assert any(record.msg == "auth.rejected" for record in event_records)
    requests = [record for record in event_records if record.msg == "http.request"]
    assert requests[-1].event_fields["credential_id"] == "test"
    assert requests[0].event_fields["credential_id"] is None
