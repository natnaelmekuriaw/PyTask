import logging

from fastapi.testclient import TestClient

from tests.observability.conftest import event_records as event_records


def test_validation_logs_the_route_template_without_identifiers(
    client: TestClient, event_records: list[logging.LogRecord],
) -> None:
    response = client.get("/api/v1/tasks/private-task-value")
    assert response.status_code == 422
    event = next(record for record in event_records if record.msg == "http.request")
    fields = event.event_fields
    assert fields["route"] == "/api/v1/tasks/{task_id}"
    assert fields["method"] == "GET" and fields["duration_seconds"] >= 0
    assert "private-task-value" not in repr(fields)
