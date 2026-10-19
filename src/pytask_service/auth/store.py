import hmac
from types import MappingProxyType

from pytask_service.auth.credentials import Credential
from pytask_service.auth.headers import AuthenticationError
from pytask_service.auth.manifest import validate_credentials
from pytask_service.auth.permissions import Principal
from pytask_service.auth.tokens import token_digest, token_key_id


class KeyStore:
    def __init__(self, keys: tuple[Credential, ...]) -> None:
        validate_credentials(keys)
        self._keys = MappingProxyType({key.key_id: key for key in keys})

    def authenticate(self, token: str) -> Principal:
        key_id = token_key_id(token)
        if key_id is None:
            raise AuthenticationError("invalid")
        credential = self._keys.get(key_id)
        expected = credential.sha256 if credential else "0" * 64
        matches = hmac.compare_digest(token_digest(token), expected)
        if credential is None or not matches:
            raise AuthenticationError("invalid")
        return Principal(credential.key_id, credential.permissions)
