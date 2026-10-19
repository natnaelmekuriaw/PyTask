import json
from dataclasses import dataclass, field

from pytask_service.auth.credentials import Credential
from pytask_service.auth.permissions import Permission
from pytask_service.auth.tokens import generate_token, token_digest


@dataclass(frozen=True, slots=True)
class IssuedKey:
    token: str = field(repr=False)
    credential: Credential

    def manifest(self) -> str:
        return json.dumps({"version": 1, "keys": [{
            "id": self.credential.key_id,
            "sha256": self.credential.sha256,
            "scopes": sorted(self.credential.permissions),
        }]}, indent=2) + "\n"


def issue_key(key_id: str, permissions: frozenset[Permission]) -> IssuedKey:
    token = generate_token(key_id)
    return IssuedKey(token, Credential(key_id, token_digest(token), permissions))
