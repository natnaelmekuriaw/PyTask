import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from pytask_service.api.handlers import register_errors


def test_unknown_routes_and_methods_share_the_error_envelope() -> None:
    app = FastAPI()
    register_errors(app)
    @app.get("/example")
    def example() -> dict[str, str]:
        return {"ok": "yes"}
    with TestClient(app) as client:
        missing = client.get("/missing")
        assert missing.status_code == 404 and missing.json()["error"]["code"] == "not_found"
        method = client.post("/example")
        assert method.status_code == 405 and "GET" in method.headers["allow"]


@pytest.mark.parametrize("database", [True, False])
def test_internal_failures_do_not_expose_exception_details(database: bool) -> None:
    app = FastAPI()
    register_errors(app)
    @app.get("/failure")
    def failure() -> None:
        if database:
            raise OperationalError("secret query", {"password": "private"}, RuntimeError("hidden"))
        raise RuntimeError("private implementation detail")
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/failure")
    assert response.status_code == (503 if database else 500)
    assert "private" not in response.text and "secret" not in response.text
