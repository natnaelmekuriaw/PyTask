from collections.abc import Iterator
from contextlib import ExitStack

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine

from pytask_service.api.app import create_app
from pytask_service.auth.issuance import issue_key
from pytask_service.auth.permissions import Permission
from pytask_service.auth.settings import AuthSettings
from pytask_service.config import Settings
from pytask_service.example_tasks import registry
from tests.auth.conftest import ClientFactory
from tests.worker.conftest import isolated_engine as isolated_engine


@pytest.fixture
def make_client(isolated_engine: Engine) -> Iterator[ClientFactory]:
    with ExitStack() as stack:
        def create(permissions: frozenset[Permission]) -> tuple[TestClient, dict[str, str]]:
            issued = issue_key("integration", permissions)
            app = create_app(
                Settings("postgresql+psycopg://u:p@localhost/db"),
                engine=isolated_engine, registry=registry,
                auth=AuthSettings(keys=(issued.credential,)),
            )
            return stack.enter_context(TestClient(app)), {
                "Authorization": f"Bearer {issued.token}",
            }
        yield create

