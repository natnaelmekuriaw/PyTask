import re

from sqlalchemy.exc import SQLAlchemyError


def postgres_state(error: SQLAlchemyError) -> str | None:
    state = getattr(getattr(error, "orig", None), "sqlstate", None)
    if isinstance(state, str) and re.fullmatch(r"[0-9A-Z]{5}", state):
        return state
    return None
