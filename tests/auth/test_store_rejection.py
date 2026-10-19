import pytest

from pytask_service.auth.headers import AuthenticationError
from pytask_service.auth.issuance import IssuedKey, issue_key
from pytask_service.auth.permissions import ALL_PERMISSIONS
from pytask_service.auth.store import KeyStore


def test_wrong_secret_and_unknown_id_are_indistinguishable(key: IssuedKey) -> None:
    store = KeyStore((key.credential,))
    for token in (
        issue_key("test", ALL_PERMISSIONS).token,
        issue_key("unknown", ALL_PERMISSIONS).token,
    ):
        with pytest.raises(AuthenticationError) as error:
            store.authenticate(token)
        assert error.value.reason == "invalid"
        assert token not in str(error.value)


def test_a_valid_secret_cannot_be_moved_to_another_key_id(key: IssuedKey) -> None:
    forged = key.token.replace("ptk_test.", "ptk_other.")
    with pytest.raises(AuthenticationError):
        KeyStore((key.credential,)).authenticate(forged)
