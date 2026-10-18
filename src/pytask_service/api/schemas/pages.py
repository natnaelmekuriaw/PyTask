from pytask_service.api.schemas.base import APIModel
from pytask_service.api.schemas.monitoring import AttemptRead


class Page[T](APIModel):
    items: list[T]
    next_cursor: str | None = None


class AttemptPage(APIModel):
    items: list[AttemptRead]
    next_after: int | None = None
