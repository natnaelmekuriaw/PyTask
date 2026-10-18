from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_context: ContextVar[dict[str, object] | None] = ContextVar(
    "operational_context", default=None
)


def current_context() -> dict[str, object]:
    return dict(_context.get() or {})


@contextmanager
def bind_context(**fields: object) -> Iterator[None]:
    token = _context.set({**current_context(), **fields})
    try:
        yield
    finally:
        _context.reset(token)
