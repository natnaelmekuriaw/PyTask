from sqlalchemy.dialects import postgresql

from pytask_service.observability.query import snapshot_statement
from pytask_service.observability.window import ObservationWindow


def test_monitoring_compiles_to_one_select_without_row_locks() -> None:
    compiled = snapshot_statement(ObservationWindow(60)).compile(
        dialect=postgresql.dialect(),
    )
    sql = str(compiled).upper()
    assert sql.startswith("SELECT ")
    assert "FOR UPDATE" not in sql and "SKIP LOCKED" not in sql
    assert "STATEMENT_TIMESTAMP()" in sql
    assert "ARGUMENTS" not in sql and "RESULT" not in sql and "ERROR" not in sql
