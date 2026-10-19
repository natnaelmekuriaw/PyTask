import pytest

from pytask_service.config import Settings
from pytask_service.db import engine
from pytask_service.db.options import DatabaseOptions


def test_connection_policy_reaches_the_engine_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    sentinel = object()

    def create(url: str, **options: object) -> object:
        captured.update(options)
        return sentinel

    monkeypatch.setattr(engine, "create_engine", create)
    options = DatabaseOptions(
        pool_size=2, max_overflow=0, pool_timeout=1.5, connect_timeout=3
    )
    settings = Settings("postgresql+psycopg://u:p@postgres/db", database=options)
    assert engine.build_engine(settings) is sentinel
    assert captured["pool_size"] == 2 and captured["max_overflow"] == 0
    assert captured["pool_timeout"] == 1.5
    assert captured["connect_args"] == {"connect_timeout": 3}
    assert captured["pool_pre_ping"] is True and captured["hide_parameters"] is True
