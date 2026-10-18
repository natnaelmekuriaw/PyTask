from sqlalchemy import text
from sqlalchemy.orm import Session


def bound_transaction(session: Session) -> None:
    session.execute(text("SET LOCAL lock_timeout = '2s'"))
    session.execute(text("SET LOCAL statement_timeout = '5s'"))
