from dataclasses import replace

from pytask_service.benchmarks.markdown_report import render_markdown
from pytask_service.benchmarks.results import RecoveryResult


def test_summary_explains_scope_and_included_overhead(report):
    text = render_markdown(report)
    assert "Complete valid run: **True**" in text
    assert "host Python engine" in text
    assert "Warmup and worker startup are excluded." in text
    assert "Submission and observation overhead are included." in text
    assert "Handlers still need idempotency." in text


def test_environment_and_errors_cannot_break_table_rows(report):
    environment = replace(report.environment, platform="host|value\nsecond line")
    result = replace(report.results[0], metrics=None, error_code="code|detail\nnext")
    text = render_markdown(replace(report, environment=environment, results=(result,)))
    assert "host\\|value second line" in text
    assert "code\\|detail next" in text
    assert "| n/a | n/a |" in text


def test_recovery_failures_show_retained_schema(report):
    recovery = RecoveryResult(
        False,
        error_code="workers_still_running",
        retained_schema="pytask_bench_" + "a" * 32,
    )
    text = render_markdown(replace(report, recovery=recovery))
    assert recovery.retained_schema in text
    assert "workers_still_running" in text
