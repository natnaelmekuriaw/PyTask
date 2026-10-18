import json
import sys

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from pytask_service.config import Settings
from pytask_service.db.engine import build_engine
from pytask_service.observability.serialization import snapshot_payload
from pytask_service.observability.service import read_snapshot
from pytask_service.observability.window import ObservationWindow


def show_stats(window_seconds: int) -> int:
    try:
        window = ObservationWindow(window_seconds)
        engine = build_engine(Settings.from_env())
        try:
            with Session(engine) as session, session.begin():
                snapshot = read_snapshot(session, window)
        finally:
            engine.dispose()
    except (ValueError, SQLAlchemyError):
        print(
            "Statistics unavailable; check configuration, database access, and migrations",
            file=sys.stderr,
        )
        return 1
    print(json.dumps(snapshot_payload(snapshot), allow_nan=False))
    return 0
