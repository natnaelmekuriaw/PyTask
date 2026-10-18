import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from pytask_service.api.handlers import register_errors
from pytask_service.api.request_logging import RequestLoggingMiddleware
from tests.observability.conftest import event_records as event_records


def test_unhandled_errors_have_a_matching_response_identifier(
    event_records: list[logging.LogRecord],
) -> None:
    app = FastAPI()
    register_errors(app)
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/failure")
    def fail() -> None:
        raise RuntimeError("private diagnostic")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/failure")
    assert response.status_code == 500
    request_id = response.headers["x-request-id"]
    events = [record for record in event_records if record.msg == "http.request"]
    assert len(events) == 1
    assert events[0].event_fields["request_id"] == request_id
    assert events[0].event_fields["status_code"] == 500
    assert "private" not in repr([r.event_fields for r in event_records])
