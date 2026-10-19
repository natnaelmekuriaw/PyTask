from collections.abc import Callable, Iterator
from contextlib import ExitStack

import pytest
from fastapi.testclient import TestClient

from pytask_service.api.app import create_app
from pytask_service.auth.issuance import IssuedKey, issue_key
from pytask_service.auth.permissions import ALL_PERMISSIONS, Permission
from pytask_service.auth.settings import AuthSettings
from pytask_service.config import Settings
from pytask_service.example_tasks import registry
from tests.api.conftest import OfflineEngine

ClientFactory = Callable[[frozenset[Permission]], tuple[TestClient, dict[str, str]]]


@pytest.fixture(autouse=True)
def clean_auth_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "PYTASK_API_AUTH_MODE",
        "PYTASK_API_KEYS",
        "PYTASK_API_KEYS_FILE",
        "PYTASK_API_DOCS_ENABLED",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def key() -> IssuedKey:
    return issue_key("test", ALL_PERMISSIONS)


@pytest.fixture
def client(key: IssuedKey) -> Iterator[TestClient]:
    app = create_app(
        Settings("postgresql+psycopg://u:p@localhost/db"),
        engine=OfflineEngine(),
        registry=registry,
        auth=AuthSettings(keys=(key.credential,), docs_enabled=True),
    )
    with TestClient(app) as http:
        yield http


@pytest.fixture
def headers(key: IssuedKey) -> dict[str, str]:
    return {"Authorization": f"Bearer {key.token}"}


@pytest.fixture
def make_client() -> Iterator[ClientFactory]:
    with ExitStack() as stack:

        def create(
            permissions: frozenset[Permission],
        ) -> tuple[TestClient, dict[str, str]]:
            issued = issue_key("restricted", permissions)
            app = create_app(
                Settings("postgresql+psycopg://u:p@localhost/db"),
                engine=OfflineEngine(),
                registry=registry,
                auth=AuthSettings(keys=(issued.credential,), docs_enabled=True),
            )
            http = stack.enter_context(TestClient(app))
            return http, {"Authorization": f"Bearer {issued.token}"}

        yield create
