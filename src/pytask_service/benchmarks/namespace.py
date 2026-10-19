import re
from uuid import uuid4


def new_schema_name() -> str:
    return "pytask_bench_" + uuid4().hex


def validate_schema_name(schema: str) -> None:
    if re.fullmatch(r"pytask_bench_[0-9a-f]{32}", schema, re.ASCII) is None:
        raise ValueError("Benchmark connections require an isolated generated schema")

