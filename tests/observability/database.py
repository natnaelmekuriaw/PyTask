from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.clock import database_now
from pytask_service.db.models import Schedule, Task, TaskAttempt
from pytask_service.observability.service import read_snapshot
from pytask_service.observability.snapshot import MonitoringSnapshot
from pytask_service.observability.window import ObservationWindow


class MonitoringDatabase:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        with Session(engine) as session:
            self.now = database_now(session)

    def task(self, **overrides: Any) -> UUID:
        identifier = uuid4()
        values = {
            "id": identifier, "name": "math.add", "arguments": {},
            "created_at": self.now - timedelta(seconds=60),
            "available_at": self.now - timedelta(seconds=30),
            **overrides,
        }
        with Session(self.engine) as session, session.begin():
            session.add(Task(**values))
        return identifier

    def attempt(self, task_id: UUID, **overrides: Any) -> UUID:
        identifier = uuid4()
        values = {
            "id": identifier, "task_id": task_id, "number": 1,
            "worker_id": "test-worker", "status": "succeeded",
            "started_at": self.now - timedelta(seconds=20),
            "queued_at": self.now - timedelta(seconds=25),
            "finished_at": self.now - timedelta(seconds=10),
            **overrides,
        }
        with Session(self.engine) as session, session.begin():
            session.add(TaskAttempt(**values))
        return identifier

    def schedule(self, **overrides: Any) -> UUID:
        identifier = uuid4()
        values = {
            "id": identifier, "name": str(identifier), "task_name": "math.add",
            "arguments": {}, "interval_seconds": 60,
            "next_run_at": self.now - timedelta(seconds=30), **overrides,
        }
        with Session(self.engine) as session, session.begin():
            session.add(Schedule(**values))
        return identifier

    def read(self, seconds: int = 3600) -> MonitoringSnapshot:
        with Session(self.engine) as session, session.begin():
            return read_snapshot(session, ObservationWindow(seconds))
