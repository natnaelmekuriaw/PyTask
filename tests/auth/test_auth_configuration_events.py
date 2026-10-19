import logging

from fastapi.testclient import TestClient

from pytask_service.api.app import create_app
from pytask_service.auth.settings import AuthSettings
from pytask_service.config import Settings
from pytask_service.example_tasks import registry
from tests.api.conftest import OfflineEngine
from tests.observability.conftest import event_records as event_records


def test_disabled_mode_emits_an_explicit_startup_warning(
    event_records: list[logging.LogRecord],
) -> None:
    app = create_app(
        Settings("postgresql+psycopg://u:p@localhost/db"),
        engine=OfflineEngine(),
        registry=registry,
        auth=AuthSettings.disabled(),
    )
    with TestClient(app):
        pass
    event = next(record for record in event_records if record.msg == "auth.configured")
    assert event.levelno == logging.WARNING
    assert event.event_fields["status"] == "disabled"
    assert event.event_fields["count"] == 0
