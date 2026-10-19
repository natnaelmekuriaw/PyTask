from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pytask_service.api.app import create_app
from pytask_service.auth.issuance import IssuedKey
from pytask_service.config import Settings
from pytask_service.example_tasks import registry
from tests.api.conftest import OfflineEngine


def test_running_api_uses_an_immutable_manifest_snapshot(
    key: IssuedKey, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "keys.json"
    path.write_text(key.manifest(), encoding="utf-8")
    monkeypatch.setenv("PYTASK_API_KEYS_FILE", str(path))
    monkeypatch.setenv("PYTASK_API_DOCS_ENABLED", "true")
    app = create_app(
        Settings("postgresql+psycopg://u:p@localhost/db"),
        engine=OfflineEngine(), registry=registry,
    )
    headers = {"Authorization": f"Bearer {key.token}"}
    with TestClient(app) as client:
        assert client.get("/openapi.json", headers=headers).status_code == 200
        path.write_text("invalid-next-configuration", encoding="utf-8")
        assert client.get("/openapi.json", headers=headers).status_code == 200
    with pytest.raises(ValueError):
        with TestClient(app):
            pass

