import pytest

from pytask_service.benchmarks.namespace import new_schema_name, validate_schema_name


def test_generated_names_are_unique_and_within_postgresql_limits():
    names = {new_schema_name() for _ in range(100)}
    assert len(names) == 100
    for name in names:
        assert len(name) < 63
        validate_schema_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "public",
        "pytask_bench_",
        "pytask_bench_" + "a" * 31,
        "pytask_bench_" + "a" * 33,
        "pytask_bench_" + "A" * 32,
        "pytask_bench_" + "g" * 32,
        "public, pg_catalog",
        '"; DROP SCHEMA public; --',
    ],
)
def test_external_or_malformed_schema_names_are_rejected(name):
    with pytest.raises(ValueError):
        validate_schema_name(name)
