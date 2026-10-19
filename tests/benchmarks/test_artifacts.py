import json

import pytest

from pytask_service.benchmarks.artifacts import _write_new, write_reports


def test_each_run_gets_a_new_directory_with_three_formats(tmp_path, report):
    first = write_reports(report, tmp_path)
    second = write_reports(report, tmp_path)
    assert first != second
    for directory in (first, second):
        assert {path.name for path in directory.iterdir()} == {
            "results.json",
            "results.csv",
            "results.md",
        }
        assert json.loads((directory / "results.json").read_text())["valid"]


def test_exclusive_writes_preserve_existing_files(tmp_path):
    target = tmp_path / "results.json"
    target.write_text("previous report")
    with pytest.raises(FileExistsError):
        _write_new(target, "replacement")
    assert target.read_text() == "previous report"


def test_serialization_failure_leaves_no_plausible_report_files(
    tmp_path, report, monkeypatch
):
    def fail(_):
        raise ValueError("invalid data")

    monkeypatch.setattr("pytask_service.benchmarks.artifacts.render_csv", fail)
    with pytest.raises(ValueError):
        write_reports(report, tmp_path)
    assert not list(tmp_path.rglob("results.*"))
