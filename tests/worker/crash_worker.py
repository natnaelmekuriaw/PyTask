import os
import re

from sqlalchemy.orm import Session

from pytask_service.config import Settings
from pytask_service.db.engine import build_engine
from pytask_service.worker.claim import claim_next


def claim_then_crash(schema: str) -> None:
    if not re.fullmatch(r"pytask_test_[a-f0-9]{32}", schema):
        raise ValueError("Crash test requires its isolated schema")
    engine = build_engine(Settings.from_env())
    with engine.connect() as connection:
        connection.exec_driver_sql(f'SET search_path TO "{schema}"')
        connection.commit()
        with Session(connection) as session, session.begin():
            claim = claim_next(session, "crashed-process")
            if claim is None:
                raise RuntimeError("Crash test found no task")
    os._exit(7)
