import sys

import pytest

from pytask_service.runtime import main as runtime


@pytest.mark.parametrize(
    "arguments",
    [
        ["api", "--reload"],
        ["worker", "--once"],
        ["scheduler", "private-value"],
        ["migrate", "downgrade"],
        ["probe"],
        ["probe", "api", "extra"],
        ["check", "extra"],
    ],
)
def test_unsupported_arguments_have_safe_errors(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    arguments: list[str],
) -> None:
    launched: list[object] = []
    monkeypatch.setattr(sys, "argv", ["runtime", *arguments])
    monkeypatch.setattr(runtime, "replace_process", launched.append)
    assert runtime.main() == 1
    assert not launched
    assert "private-value" not in capsys.readouterr().err


def test_check_role_routes_to_the_read_only_database_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probes: list[str] = []
    monkeypatch.setattr(sys, "argv", ["runtime", "check"])
    monkeypatch.setattr(runtime, "run_probe", lambda kind: probes.append(kind) or 0)
    assert runtime.main() == 0 and probes == ["database"]
