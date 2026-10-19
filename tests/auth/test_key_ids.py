import pytest

from pytask_service.auth.tokens import generate_token, token_key_id


@pytest.mark.parametrize(
    "key_id", ["", "Upper", "../key", "a.b", "x\ny", "é", "-x", "a" * 49]
)
def test_invalid_key_identifiers_are_rejected(key_id: str) -> None:
    with pytest.raises(ValueError, match="Key ID"):
        generate_token(key_id)


def test_maximum_length_key_identifier_round_trips() -> None:
    key_id = "a" * 48
    assert token_key_id(generate_token(key_id)) == key_id
