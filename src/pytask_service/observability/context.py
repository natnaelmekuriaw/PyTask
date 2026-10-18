from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_context: ContextVar[dict[str, object]] = ContextVar("operational_context", default={})


def current_context() -> dict[str, object]:
    return dict(_context.get())


@contextmanager
def bind_context(**fields: object) -> Iterator[None]:
    token = _context.set({**_context.get(), **fields})
    try:
        yield
    finally:
        _context.reset(token)
