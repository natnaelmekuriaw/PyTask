# Investigate monitoring symptoms

## Ready tasks keep accumulating

Compare `ready` and `oldest_ready_age_seconds` across observations. Confirm a
worker is running with the same database and registry. Check its task claim
and finish events. A healthy API readiness response only checks database
access; it does not establish that a worker is consuming tasks.

## Pending tasks are not ready

Check `delayed`, `retry_wait`, and `exhausted_pending`. Future availability
and retry backoff are expected waiting states. Exhausted pending rows indicate
an inconsistent queue state that needs investigation. Reading statistics does
not repair it.

## Running tasks have expired leases

An expired lease does not prove whether the old handler stopped. A worker
recovers expired work on its next poll, and handlers must tolerate repeated
execution. Look for `worker.leases_recovered`, `task.lease_lost`, and abandoned
attempts. A running row with no lease is counted separately.

## Due schedules keep accumulating

Keep a scheduler running against the same database. Paused definitions do
not count as due. A schedule counts once even when it missed many intervals;
dispatch still follows the latest-due policy documented in the scheduling
guide. Workers execute dispatched tasks separately.

## Queue wait or execution mean is null

Read `samples` first. Null means there are no valid measurements for that
summary and window. Historical attempts may lack eligibility timestamps.
Running attempts have no completed execution duration; abandoned attempts do
not enter execution timing. Widening the window can reveal older samples.

## The endpoint returns 503 or the command reports unavailable

Check the connection with `pytask-service check-db`, then check the migration
revision and `alembic check`. Summary queries have a five-second statement
timeout and two-second lock timeout. Large retained histories and database
contention can reach those limits.

Queue totals scan retained task rows. Timestamp indexes support windowed
attempt reads, but do not make aggregate reads free. Avoid aggressive polling;
measure query time and database load before choosing a polling frequency.

## A committed task has no corresponding event

Events are best effort. Check the log level and stderr destination, then use
the persisted task and attempt history. A process can exit between committing
and emitting an event. INFO events are suppressed at WARNING and above.

For slow test runs, `pytest -vv --durations=10` shows the active test and
reports the slowest setup, call, and cleanup phases after completion. PostgreSQL
tests create isolated schemas, and process tests include deliberate waits.
