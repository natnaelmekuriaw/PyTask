# Benchmark design

The suite measures the task engine through its Python submission and worker
interfaces. It uses host Python worker processes and the configured PostgreSQL
server. HTTP, API authentication, Docker worker performance, and scheduling
throughput are outside this measurement.

Every case owns a fresh randomly named schema. Worker connections use only
that schema as their search path. Existing application tables are never used.
The coordinator creates current model tables and indexes there; migrations
remain part of the preceding deployment verification.

Workers start with the spawn method and signal readiness before warmup.
Warmup tasks complete before timing begins. One producer submits the measured
batch with one committed transaction per task while workers consume it.
Elapsed time ends when the coordinator observes the whole batch complete.
This includes submission, polling, database work, and process execution.
The production worker still starts a fresh handler process for each task.

Repeat order rotates worker counts to reduce ordering bias. Reports retain
every run, including failures, and summarize only complete valid repetitions.
A small default workload is a local baseline, not a capacity promise.
Database timestamps measure task and attempt intervals; monotonic clocks
measure coordinator elapsed time. Negative intervals invalidate observations.

The recovery check kills a worker after it claims a task and before launching
its handler. A replacement waits for natural lease expiry and executes the
same task. It checks abandonment and success history separately from
throughput. It does not demonstrate exactly-once side effects.

Cleanup stops owned workers before dropping owned schemas. If workers cannot
be stopped, retain the schema and report its name. A report never contains
database URLs, credentials, task arguments, results, or raw database errors.

References: [Python spawn](https://docs.python.org/3.12/library/multiprocessing.html),
[PostgreSQL schemas](https://www.postgresql.org/docs/17/ddl-schemas.html), and
[SQLAlchemy PostgreSQL](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html).

