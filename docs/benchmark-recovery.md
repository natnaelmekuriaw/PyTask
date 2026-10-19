# Benchmark recovery check

Recovery runs separately after every throughput case passes. It uses one
fresh schema and one task with a two-attempt limit.

1. A real worker claims and commits the task with a three-second lease and
   a half-second heartbeat interval.
2. Its executor signals that execution was reached and exits with code 7
   before launching a handler process.
3. The coordinator confirms that its owned victim process exited.
4. A replacement production worker starts and waits for the stored lease to
   expire naturally. No stored timestamps are changed.
5. The replacement records the first attempt as abandoned and completes
   the task on its second attempt.

The tiny retry delay uses the production full-jitter retry path. The
replacement uses the regular worker lease policy; the shortened lease
belongs to the victim only.

The check verifies one successful task, exactly two attempt numbers, distinct
claim tokens, matching task identity, nonnegative stored timing intervals,
the expected result and outcomes `abandoned, succeeded`.

## Recovery time

The reported interval begins after the coordinator observes the victim's
exit and ends when it observes task completion. It includes replacement
startup, lease expiry, retry eligibility, handler execution, database work
and completion polling. It is not a general recovery latency guarantee.

This covers loss before handler execution. It does not demonstrate safety
for external side effects performed before a worker dies. Delivery remains
at least once, and application handlers still need idempotency.

## Process and schema ownership

The coordinator stops and closes only the processes it created. It closes
worker groups before dropping their generated schema. An unreaped worker
causes schema retention and a failed report. Cleanup errors also record the
retained schema.

A hard process or machine termination can bypass Python cleanup entirely,
so a report is not guaranteed after a forced shutdown. Inspect local
processes and the database before removing an abandoned benchmark schema.
Never use a broad prefix-based drop against a shared database.

See [troubleshooting](benchmark-troubleshooting.md) for retained schemas and
[the reliability contract](reliability.md) for application delivery semantics.
