import subprocess
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from pytask_service.benchmarks import revision


@pytest.mark.parametrize("status,dirty", [(0, False), (1, True), (128, None)])
def test_revision_and_tracked_dirty_state_are_recorded(monkeypatch, status, dirty):
    run = MagicMock(
        side_effect=[
            SimpleNamespace(returncode=0, stdout="a" * 40 + "\n"),
            SimpleNamespace(returncode=status),
        ]
    )
    monkeypatch.setattr(revision.subprocess, "run", run)
    assert revision.source_revision() == ("a" * 40, dirty)
    assert all(call.kwargs["timeout"] == 2 for call in run.call_args_list)


@pytest.mark.parametrize(
    "error", [OSError("git absent"), subprocess.TimeoutExpired("git", 2)]
)
def test_unavailable_git_returns_unknown_metadata(monkeypatch, error):
    monkeypatch.setattr(revision.subprocess, "run", MagicMock(side_effect=error))
    assert revision.source_revision() == (None, None)


def test_non_repository_diagnostics_are_not_treated_as_revisions(monkeypatch):
    run = MagicMock(
        return_value=SimpleNamespace(returncode=128, stdout="private diagnostic")
    )
    monkeypatch.setattr(revision.subprocess, "run", run)
    assert revision.source_revision() == (None, None)
    run.assert_called_once()
