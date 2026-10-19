import pytest

from pytask_service.auth.headers import AuthenticationError
from pytask_service.auth.issuance import issue_key
from pytask_service.auth.permissions import Permission
from pytask_service.auth.store import KeyStore


def test_multiple_keys_resolve_to_distinct_principals() -> None:
    read = issue_key("reader", frozenset({Permission.TASKS_READ}))
    write = issue_key("submitter", frozenset({Permission.TASKS_SUBMIT}))
    store = KeyStore((read.credential, write.credential))
    assert store.authenticate(read.token).permissions == read.credential.permissions
    assert store.authenticate(write.token).key_id == "submitter"


def test_removing_a_key_revokes_it_in_a_new_store() -> None:
    old = issue_key("old", frozenset({Permission.TASKS_READ}))
    new = issue_key("new", frozenset({Permission.TASKS_READ}))
    store = KeyStore((new.credential,))
    with pytest.raises(AuthenticationError):
        store.authenticate(old.token)
    assert store.authenticate(new.token).key_id == "new"
