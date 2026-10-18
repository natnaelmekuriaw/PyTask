import pytest
from fastapi.testclient import TestClient

from pytask_service.api.routes import monitoring
from tests.observability.factories import empty_snapshot


def test_monitoring_uses_requested_window_and_disables_caching(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    windows: list[int] = []

    def read(session: object, window: object) -> object:
        windows.append(window.seconds)
        return empty_snapshot(window.seconds)

    monkeypatch.setattr(monitoring, "read_snapshot", read)
    response = client.get("/api/v1/monitoring?window_seconds=60")
    assert response.status_code == 200, response.text
    assert windows == [60]
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["queue"]["total"] == 0
    assert body["attempts"]["execution"]["mean_seconds"] is None
    assert body["window_seconds"] == 60
    assert set(body) == {
        "observed_at",
        "window_seconds",
        "window_start",
        "queue",
        "attempts",
        "schedules",
    }
