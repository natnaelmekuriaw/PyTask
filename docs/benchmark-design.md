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

## Connection and process boundaries

Every worker uses an independent SQLAlchemy engine with one pooled connection
and one overflow connection for heartbeat work. Search path is set at connect
time to the exact generated schema, with no public fallback. The coordinator
checks both `current_schema()` and `search_path` before creating model tables.
The schema name must match the generated namespace before any DDL is issued.

Worker queries have a five-second statement timeout and a two-second lock
timeout. Schema DDL has the same bounds. Connections have a five-second
connect timeout in scoped worker engines. Coordinator connection settings
follow the existing database configuration. Phase deadlines are checked
between these operations; they do not interrupt an in-flight database call.

Warmup and measured batches have independent deadlines. Workers remain alive
through both phases, and readiness confirms engine/registry setup before
timing. Event logging is set to WARNING in benchmark workers to exclude
per-task informational log writes. The handler process path is unchanged.

## Validity and reproducibility

Reference results are computed before the measured window. The final snapshot
and result checks occur after the completion observation stops the timer.
Validity requires the exact submitted task population, exact result types and
values, and one successful attempt per task. Distinct task and claim identities
are checked before calculating metrics. Recovery uses its separate two-attempt
contract.

Database timestamp arithmetic normalizes offsets to UTC. Historical missing,
naive or reversed timestamps invalidate the observation. Coordinator timing
uses monotonic clocks and does not depend on wall-clock adjustments; database
timestamp intervals still reflect the database server's clock.

Model tables and indexes are identical to the current code, but table contents
are empty at case setup. Small warmup batches do not guarantee all workers have
run a handler. The one-producer design, completion polling and default handler
process startup cost are intentional parts of this baseline. There are no
hardware-specific assertions or committed example throughput numbers.

For an operator's sequence see [benchmarks](benchmarks.md); for field meanings
and comparison limits see [report formats](benchmark-results.md).

References: [Python spawn](https://docs.python.org/3.12/library/multiprocessing.html),
[PostgreSQL schemas](https://www.postgresql.org/docs/17/ddl-schemas.html), and
[SQLAlchemy PostgreSQL](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html).
