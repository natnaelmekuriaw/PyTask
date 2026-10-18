# Contributing to PyTask

Thanks for taking the time to contribute. Start with an issue for substantial
changes so the behavior and scope are clear before implementation.

## Development

Follow the local setup in the [README](README.md). Run linting, formatting,
type checking, and tests before opening a pull request:

```powershell
.\.venv\Scripts\ruff check .
.\.venv\Scripts\ruff format --check .
.\.venv\Scripts\mypy
.\.venv\Scripts\pytest -q
```

Tests that need PostgreSQL run when `PYTASK_DATABASE_URL` is set. Use the local
Compose database or a disposable test database; integration tests may change
its contents as the project grows. Run `alembic upgrade head` first. Worker
integration tests create and remove their own PostgreSQL schemas; the database
user needs permission to create schemas.

Worker changes should cover both a single worker and competing claims where
concurrency matters. Keep the claim transaction short and run task handlers
outside it. Check child-process behavior on Windows as well as Linux when
changing process execution or shutdown.

For reliability changes, cover lease expiry and stale claim tokens as well as
successful execution. Reusing a worker ID must not let an old attempt renew or
finish a new one. Check retry exhaustion, timeout cleanup, and attempt history
when changing task transitions. Expire stored leases directly in integration
tests instead of waiting for wall-clock expiry; use bounded waits when the
process or heartbeat behavior itself is under test.

See the [worker design](docs/worker-design.md) for transaction boundaries and
the [reliability contract](docs/reliability.md) for delivery semantics. Stop
workers before schema upgrades; the [upgrade guide](docs/reliability-upgrade.md)
includes migration checks and examples.

Use `feat/short-name` for feature branches and `fix/short-name` for fixes.
Keep commits focused and describe the change in a short subject line.

## Pull requests

Explain the behavior you changed, how you checked it, and any migration or
compatibility concerns. Add tests for behavior that could regress. For schema
changes, include an Alembic migration and check both upgrade and downgrade.
