import os
from dataclasses import dataclass, field
from enum import StrEnum

from pytask_service.auth.credentials import Credential
from pytask_service.auth.manifest import parse_manifest, validate_credentials
from pytask_service.environment import read_secret


class AuthMode(StrEnum):
    REQUIRED = "required"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class AuthSettings:
    mode: AuthMode = AuthMode.REQUIRED
    keys: tuple[Credential, ...] = field(default=(), repr=False)
    docs_enabled: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.mode, AuthMode) or type(self.docs_enabled) is not bool:
            raise ValueError("Invalid API authentication settings")
        if not isinstance(self.keys, tuple) or any(
            not isinstance(key, Credential) for key in self.keys
        ):
            raise ValueError("API keys must be an immutable credential tuple")
        if self.mode is AuthMode.REQUIRED:
            validate_credentials(self.keys)
        elif self.keys:
            raise ValueError("Disabled authentication must not configure API keys")

    @classmethod
    def disabled(cls) -> "AuthSettings":
        return cls(mode=AuthMode.DISABLED, docs_enabled=True)

    @classmethod
    def from_env(cls) -> "AuthSettings":
        try:
            mode = AuthMode(os.environ.get("PYTASK_API_AUTH_MODE", "required").strip())
        except ValueError:
            raise ValueError(
                "PYTASK_API_AUTH_MODE must be required or disabled"
            ) from None
        raw = read_secret("PYTASK_API_KEYS")
        if mode is AuthMode.DISABLED and raw:
            raise ValueError("Remove PYTASK_API_KEYS when authentication is disabled")
        keys = parse_manifest(raw) if raw else ()
        docs = os.environ.get(
            "PYTASK_API_DOCS_ENABLED", "true" if mode is AuthMode.DISABLED else "false"
        ).strip()
        if docs not in {"true", "false"}:
            raise ValueError("PYTASK_API_DOCS_ENABLED must be true or false")
        return cls(mode=mode, keys=keys, docs_enabled=docs == "true")
