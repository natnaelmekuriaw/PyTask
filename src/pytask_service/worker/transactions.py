from sqlalchemy import text
from sqlalchemy.orm import Session

from pytask_service.db.clock import database_now as database_now


def bound_lease_transaction(session: Session) -> None:
    session.execute(text("SET LOCAL lock_timeout = '2s'"))
    session.execute(text("SET LOCAL statement_timeout = '5s'"))
