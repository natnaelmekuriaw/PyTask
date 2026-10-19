import pytest

from pytask_service.auth.tokens import token_key_id


@pytest.mark.parametrize("token", [
    "", "ptk_demo.", "ptk_demo." + "A" * 42, "ptk_demo." + "A" * 44,
    "ptk_demo." + "A" * 42 + "B", "ptk_demo." + "A" * 42 + "=",
    "ptk_demo." + "A" * 42 + "é", "ptk_demo." + "A" * 43 + "\n",
    "ptk_demo." + "A" * 10000, "other_demo." + "A" * 43,
])
def test_invalid_tokens_have_no_key_identity(token: str) -> None:
    assert token_key_id(token) is None

