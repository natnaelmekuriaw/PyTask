import pytest

from pytask_service.environment import read_secret


def test_direct_and_file_sources_are_never_selected_implicitly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTASK_DATABASE_URL", "private-direct-url")
    monkeypatch.setenv("PYTASK_DATABASE_URL_FILE", "private-nonexistent-path")
    with pytest.raises(ValueError) as failure:
        read_secret("PYTASK_DATABASE_URL")
    assert (
        str(failure.value)
        == "Set only one of PYTASK_DATABASE_URL and PYTASK_DATABASE_URL_FILE"
    )
    assert "private" not in str(failure.value)
