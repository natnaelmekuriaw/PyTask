from sqlalchemy import text
from sqlalchemy.orm import Session

from pytask_service.db.transactions import bound_transaction
from pytask_service.observability.query import snapshot_statement
from pytask_service.observability.report import build_snapshot
from pytask_service.observability.snapshot import MonitoringSnapshot
from pytask_service.observability.window import ObservationWindow


def read_snapshot(
    session: Session, window: ObservationWindow | None = None
) -> MonitoringSnapshot:
    window = window or ObservationWindow()
    session.execute(text("SET TRANSACTION READ ONLY"))
    bound_transaction(session)
    row = session.execute(snapshot_statement(window)).mappings().one()
    return build_snapshot(row, window)
