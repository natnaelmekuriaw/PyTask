from dataclasses import dataclass
from enum import StrEnum


class Permission(StrEnum):
    TASKS_READ = "tasks:read"
    TASKS_SUBMIT = "tasks:submit"
    SCHEDULES_READ = "schedules:read"
    SCHEDULES_WRITE = "schedules:write"
    MONITORING_READ = "monitoring:read"
    DOCS_READ = "docs:read"


ALL_PERMISSIONS = frozenset(Permission)


@dataclass(frozen=True, slots=True)
class Principal:
    key_id: str | None
    permissions: frozenset[Permission]

    def permits(self, required: set[Permission]) -> bool:
        return required <= self.permissions
