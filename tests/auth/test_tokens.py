from pytask_service.auth.issuance import issue_key
from pytask_service.auth.permissions import ALL_PERMISSIONS
from pytask_service.auth.tokens import generate_token, token_digest, token_key_id


def test_generated_keys_are_unique_and_identify_their_owner() -> None:
    first, second = generate_token("billing"), generate_token("billing")
    assert first != second
    assert token_key_id(first) == "billing"
    assert len(first.split(".")[1]) == 43


def test_issuance_stores_only_a_digest_in_the_manifest() -> None:
    issued = issue_key("billing", ALL_PERMISSIONS)
    assert issued.token not in issued.manifest()
    assert token_digest(issued.token) in issued.manifest()
    assert issued.token not in repr(issued)
    assert issued.credential.sha256 not in repr(issued.credential)

