from dataclasses import dataclass

from pytask_service.runtime.roles import Role


@dataclass(frozen=True, slots=True)
class ProcessCommand:
    role: Role
    argv: tuple[str, ...]
