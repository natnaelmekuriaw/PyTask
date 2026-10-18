from collections.abc import Callable
from uuid import UUID

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pytask_service.db.models import Task
from pytask_service.scheduling.dispatch import dispatch_due

pytestmark = pytest.mark.integration


def test_database_rejects_duplicate_occurrence_identity(
    isolated_engine: Engine, schedule_factory: Callable[..., UUID]
) -> None:
    schedule_factory()
    with Session(isolated_engine) as session, session.begin():
        occurrence = dispatch_due(session)[0]
    with pytest.raises(IntegrityError):
        with Session(isolated_engine) as session, session.begin():
            session.add(
                Task(
                    name="math.add",
                    arguments={},
                    schedule_id=occurrence.schedule_id,
                    scheduled_for=occurrence.scheduled_for,
                )
            )
            session.flush()


def test_database_rejects_partial_schedule_origin(
    isolated_engine: Engine, schedule_factory: Callable[..., UUID]
) -> None:
    schedule_id = schedule_factory()
    with pytest.raises(IntegrityError):
        with Session(isolated_engine) as session, session.begin():
            session.add(Task(name="math.add", arguments={}, schedule_id=schedule_id))
            session.flush()
