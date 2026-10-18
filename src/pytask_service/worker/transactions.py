from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session


def database_now(session: Session) -> datetime:
    value = session.scalar(select(func.clock_timestamp()))
    if not isinstance(value, datetime):
        raise RuntimeError("PostgreSQL did not return its current timestamp")
    return value


def bound_lease_transaction(session: Session) -> None:
    session.execute(text("SET LOCAL lock_timeout = '2s'"))
    session.execute(text("SET LOCAL statement_timeout = '5s'"))
