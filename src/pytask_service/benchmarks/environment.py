import os
import platform
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version


@dataclass(frozen=True, slots=True)
class Environment:
    python: str
    implementation: str
    platform: str
    logical_cpus: int | None
    packages: dict[str, str | None]
    postgres: str | None = None
    revision: str | None = None
    tracked_changes: bool | None = None
    process_start_method: str = "spawn"


def host_environment() -> Environment:
    packages: dict[str, str | None] = {}
    for package in ("pytask-service", "SQLAlchemy", "psycopg"):
        try:
            packages[package] = version(package)
        except PackageNotFoundError:
            packages[package] = None
    return Environment(
        platform.python_version(),
        platform.python_implementation(),
        platform.platform(),
        os.cpu_count(),
        packages,
    )
