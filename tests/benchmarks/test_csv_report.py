import csv
from dataclasses import replace
from io import StringIO

from pytask_service.benchmarks.csv_report import COLUMNS, render_csv


def test_csv_has_explicit_units_and_converts_seconds_to_milliseconds(report):
    reader = csv.DictReader(StringIO(render_csv(report)))
    assert tuple(reader.fieldnames) == COLUMNS
    row = next(reader)
    assert float(row["latency_p95_ms"]) == 3000
    assert float(row["queue_wait_p95_ms"]) == 1000
    assert float(row["attempt_p95_ms"]) == 2000
    assert float(row["throughput_per_second"]) == 0.5


def test_invalid_rows_do_not_publish_partial_metrics(report):
    bad = replace(report.results[0], error_code="worker_exited")
    row = next(csv.DictReader(StringIO(render_csv(replace(report, results=(bad,))))))
    assert row["valid"] == "False"
    assert row["error_code"] == "worker_exited"
    assert (
        row["submitted"] == row["elapsed_seconds"] == row["throughput_per_second"] == ""
    )
