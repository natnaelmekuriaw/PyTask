import re
from dataclasses import dataclass, field

from pytask_service.auth.permissions import Permission
from pytask_service.auth.tokens import validate_key_id


@dataclass(frozen=True, slots=True)
class Credential:
    key_id: str
    sha256: str = field(repr=False)
    permissions: frozenset[Permission]

    def __post_init__(self) -> None:
        validate_key_id(self.key_id)
        if (
            not isinstance(self.sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", self.sha256, re.ASCII) is None
        ):
            raise ValueError("Credential sha256 must be a lowercase SHA-256 hex digest")
        if (
            not isinstance(self.permissions, frozenset)
            or not self.permissions
            or any(not isinstance(item, Permission) for item in self.permissions)
        ):
            raise ValueError("Credential permissions must be a nonempty permission set")
