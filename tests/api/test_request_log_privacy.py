import logging

from fastapi.testclient import TestClient

from tests.observability.conftest import event_records as event_records


def test_unmatched_paths_and_query_values_are_not_logged(
    client: TestClient, event_records: list[logging.LogRecord],
) -> None:
    response = client.get("/private-token?password=private-value")
    event = next(record for record in event_records if record.msg == "http.request")
    assert event.event_fields["route"] == "unmatched"
    assert event.event_fields["status_code"] == 404
    assert event.event_fields["request_id"] == response.headers["x-request-id"]
    assert "private" not in repr(event.event_fields)
