import os
from dataclasses import dataclass

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    registry_path: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        database_url = os.environ.get("PYTASK_DATABASE_URL", "").strip()
        if not database_url:
            raise ValueError("PYTASK_DATABASE_URL is required")

        try:
            url = make_url(database_url)
        except ArgumentError as exc:
            raise ValueError("PYTASK_DATABASE_URL is not a valid database URL") from exc

        if url.drivername != "postgresql+psycopg" or not url.database:
            raise ValueError(
                "PYTASK_DATABASE_URL must use postgresql+psycopg and name a database"
            )

        registry_path = os.environ.get("PYTASK_REGISTRY", "").strip() or None
        return cls(database_url=database_url, registry_path=registry_path)
