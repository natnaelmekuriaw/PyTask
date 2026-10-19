from dataclasses import asdict
from importlib.metadata import PackageNotFoundError

from pytask_service.benchmarks import environment


def test_missing_package_versions_are_reported_as_unknown(monkeypatch):
    def missing(name):
        raise PackageNotFoundError(name)

    monkeypatch.setattr(environment, "version", missing)
    monkeypatch.setattr(environment.os, "cpu_count", lambda: None)
    result = environment.host_environment()
    assert set(result.packages) == {"pytask-service", "SQLAlchemy", "psycopg"}
    assert all(value is None for value in result.packages.values())
    assert result.logical_cpus is None


def test_environment_has_no_hostname_or_database_fields():
    fields = asdict(environment.host_environment())
    assert "hostname" not in fields
    assert "database_url" not in fields
    assert fields["process_start_method"] == "spawn"
