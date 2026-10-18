import json
import re
import sys

from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from pytask_service.config import Settings
from pytask_service.db.engine import build_engine
from pytask_service.observability.serialization import snapshot_payload
from pytask_service.observability.service import read_snapshot
from pytask_service.observability.window import ObservationWindow


def show_stats(window_seconds: int) -> int:
    try:
        window = ObservationWindow(window_seconds)
        settings = Settings.from_env()
    except ValueError as error:
        print(f"Statistics unavailable: {error}", file=sys.stderr)
        return 1

    try:
        engine = build_engine(settings)
        try:
            with Session(engine) as session, session.begin():
                snapshot = read_snapshot(session, window)
        finally:
            engine.dispose()
    except SQLAlchemyError as error:
        print(f"Statistics unavailable: {_database_hint(error)}", file=sys.stderr)
        return 1
    print(json.dumps(snapshot_payload(snapshot), allow_nan=False))
    return 0


def _database_hint(error: SQLAlchemyError) -> str:
    state = getattr(getattr(error, "orig", None), "sqlstate", None)
    if isinstance(state, str):
        if state in {"42P01", "42703"}:
            return (
                "Monitoring tables or columns are missing; "
                "apply migrations with alembic upgrade head."
            )
        if state in {"28000", "28P01"}:
            return "PostgreSQL rejected the connection credentials."
        if state == "42501":
            return "PostgreSQL denied access; check database user permissions."
        if state == "57014":
            return (
                "The statistics query timed out or was canceled; check database load."
            )
        if state == "55P03":
            return "The statistics query could not acquire a database lock in time."
        if re.fullmatch(r"[0-9A-Z]{5}", state):
            return f"PostgreSQL rejected the statistics query (SQLSTATE {state})."
    if isinstance(error, OperationalError):
        return (
            "Database operation failed; run pytask-service check-db in this terminal."
        )
    return "The statistics query failed; check database access and migrations."
