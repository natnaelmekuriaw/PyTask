from fastapi import FastAPI
from fastapi.testclient import TestClient

from pytask_service.api.handlers import register_errors


def test_unexpected_failure_responses_exclude_private_diagnostics() -> None:
    app = FastAPI()
    register_errors(app)

    @app.get("/fail")
    def fail() -> None:
        raise RuntimeError("private-token-value")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/fail")
    assert response.status_code == 500
    assert "private-token-value" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
