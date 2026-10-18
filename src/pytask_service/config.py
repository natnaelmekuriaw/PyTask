import os
from dataclasses import dataclass, field

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from pytask_service.db.options import DatabaseOptions
from pytask_service.environment import read_secret


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = field(repr=False)
    registry_path: str | None = None
    database: DatabaseOptions = field(default_factory=DatabaseOptions)

    @classmethod
    def from_env(cls) -> "Settings":
        database_url = read_secret("PYTASK_DATABASE_URL")
        if not database_url:
            raise ValueError("PYTASK_DATABASE_URL is required")

        if "\x00" in database_url:
            raise ValueError("PYTASK_DATABASE_URL is not a valid database URL")
        try:
            url = make_url(database_url)
        except ArgumentError as exc:
            raise ValueError("PYTASK_DATABASE_URL is not a valid database URL") from exc

        if url.drivername != "postgresql+psycopg" or not url.database:
            raise ValueError(
                "PYTASK_DATABASE_URL must use postgresql+psycopg and name a database"
            )

        registry_path = os.environ.get("PYTASK_REGISTRY", "").strip() or None
        return cls(
            database_url=database_url,
            registry_path=registry_path,
            database=DatabaseOptions.from_env(),
        )
