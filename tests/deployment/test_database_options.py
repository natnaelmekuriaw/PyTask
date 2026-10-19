import pytest

from pytask_service.db.options import DatabaseOptions


@pytest.mark.parametrize(
    "field,value",
    [
        ("pool_size", 0),
        ("pool_size", True),
        ("max_overflow", -1),
        ("max_overflow", 101),
        ("pool_recycle", 29),
        ("connect_timeout", 31),
        ("pool_timeout", float("nan")),
        ("pool_timeout", True),
        ("pool_timeout", 0),
    ],
)
def test_invalid_connection_budgets_are_rejected(field: str, value: object) -> None:
    with pytest.raises(ValueError, match=field):
        DatabaseOptions(**{field: value})


def test_zero_overflow_and_custom_timeouts_are_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTASK_DB_POOL_SIZE", "2")
    monkeypatch.setenv("PYTASK_DB_MAX_OVERFLOW", "0")
    monkeypatch.setenv("PYTASK_DB_CONNECT_TIMEOUT", "3")
    monkeypatch.setenv("PYTASK_DB_POOL_TIMEOUT", "0.5")
    options = DatabaseOptions.from_env()
    assert (options.pool_size, options.max_overflow, options.connect_timeout) == (
        2,
        0,
        3,
    )
    assert options.pool_timeout == 0.5
