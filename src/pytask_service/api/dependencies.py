from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from pytask_service.api.resources import APIResources, get_resources

ResourcesDep = Annotated[APIResources, Depends(get_resources)]


def get_session(resources: ResourcesDep) -> Iterator[Session]:
    with Session(resources.engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
