import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    alembic_config: Path

    @classmethod
    def from_env(cls) -> "RuntimePaths":
        raw = os.environ.get("PYTASK_ALEMBIC_CONFIG", "alembic.ini").strip()
        try:
            path = Path(raw).resolve()
            valid = bool(raw) and path.is_file()
        except (OSError, ValueError):
            valid = False
        if not valid:
            raise ValueError("PYTASK_ALEMBIC_CONFIG must point to an existing file")
        return cls(path)
