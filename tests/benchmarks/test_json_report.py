import json
from dataclasses import replace

import pytest

from pytask_service.benchmarks.json_report import render_json
from pytask_service.benchmarks.records import TaskRecord


def test_json_contains_metrics_without_payloads_or_connection_details(report):
    document = json.loads(render_json(report))
    assert document["valid"] is True
    assert document["cases"][0]["metrics"]["submitted"] == 2
    assert document["options"]["workloads"] == ["noop"]
    encoded = render_json(report)
    for field in ("database_url", "arguments", "hostname", "password"):
        assert field not in encoded


def test_nonfinite_report_values_are_not_serialized(report):
    bad_metrics = replace(report.results[0].metrics, elapsed_seconds=float("nan"))
    result = replace(report.results[0], metrics=bad_metrics)
    with pytest.raises(ValueError):
        render_json(replace(report, results=(result,)))


def test_observation_repr_does_not_expose_task_results(observation):
    record: TaskRecord = replace(observation.tasks[0], result="private-result-marker")
    assert "private-result-marker" not in repr(record)
