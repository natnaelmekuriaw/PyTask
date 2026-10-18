# Scheduling design

PyTask supports delayed tasks and recurring schedules. Both use the same
PostgreSQL queue and worker engine. Scheduling does not execute handlers.

## Delayed tasks

`submit --delay SECONDS` adds a delay to PostgreSQL's current time. Delays
may be fractional, from zero through 31536000 seconds (365 days).
`submit --run-at TIMESTAMP` accepts an ISO 8601 timestamp with an explicit UTC
offset. Inputs are normalized to UTC; naive timestamps are rejected. A time
in the past makes the task immediately eligible.

Both options set `tasks.available_at`. Workers already exclude tasks whose
eligibility time has not arrived. A delayed task uses no attempts until it is
claimed, and needs no scheduler process. `--delay` and `--run-at` cannot be
combined. The execution timeout begins when the worker starts its task
process, so time spent waiting in the queue does not consume it.

## Fixed intervals

A schedule stores a unique name, registered task name, validated JSON
arguments, execution policy, interval, and next due timestamp. Intervals are
whole seconds from 1 through 31536000. The first occurrence defaults to the
database time at creation; `--start-at` supplies an explicit first due time.

The cadence is anchored to that first timestamp. If a schedule starts at
12:00 with a 60-second interval, its occurrences are 12:00, 12:01, and so on,
regardless of scheduler polling delay or handler duration. UTC intervals do
not represent local calendar rules. Cron expressions and daylight-saving
timezone rules are outside this stage.

## Missed occurrences

Each scheduler tick selects the latest due occurrence and skips older missed
ones. For the schedule above, a restart at 12:05:20 enqueues the 12:05
occurrence and moves its cursor to 12:06. It does not enqueue the five older
occurrences or shift the cadence to 12:06:20.

This policy avoids a burst after downtime. It does not guarantee execution
of every historical interval. Applications that need every period processed
should use their own business records to track unfinished periods.

## Dispatch transaction

A scheduler locks a bounded batch of unpaused, due schedules using
`FOR UPDATE SKIP LOCKED`, ordered by next due time and ID. Another scheduler
can work on different rows without a leader election step.

For each selected schedule, dispatch inserts a pending task and advances the
schedule cursor in the same transaction. The task copies the definition's
arguments and retry/timeout policy, and stores its `schedule_id` and logical
`scheduled_for` timestamp. A unique constraint on those two fields protects
occurrence identity. Conflict handling returns the existing task without
resetting its state, result, or attempts.

If the transaction rolls back, neither the inserted tasks nor the advanced
cursors remain. Reports are printed after the batch commits. A report with
`created: false` means the occurrence already had a task, such as when an
existing cursor was replayed. Deduplication relies on retained task records;
this stage has no task-history deletion command.

## Pause, resume, and overlap

Pause and resume lock the same schedule row used by dispatch, refreshing its
state after acquiring the lock. A completed pause prevents subsequent
dispatches for that schedule. Tasks committed before the pause remain queued
and may still run. Pause is not task cancellation.

Resume preserves the original cursor and cadence. If occurrences were missed
while paused, the next tick applies the same latest-due policy. Repeating a
pause or resume is safe. `create --paused` allows a definition to be inspected
before dispatch begins.

Each occurrence is an independent task. Long-running work or retries can
overlap later occurrences when several workers are running. Use business
locks or idempotency keys inside handlers where overlap must be controlled.
Retries and crash recovery reuse the same task ID and occurrence identity;
they do not create another recurring occurrence.

## Operating the scheduler

`scheduler --once` dispatches at most one batch; it does not wait for future
due times or execute the tasks. The continuous command drains full batches
and waits between partial or empty batches. Defaults are 100 schedules per
batch and a one-second polling interval. Batch size is limited to 1000.

Ctrl+C or SIGTERM requests shutdown after the active batch. Database lock and
statement timeouts bound individual maintenance queries. A database error
rolls back the active transaction and exits the command with a nonzero
status; restart it after resolving the error.

Schedule creation imports the configured registry to validate the handler and
arguments. The scheduler itself only enqueues saved definitions and does not
need `PYTASK_REGISTRY`. Workers must have the referenced handlers deployed.
All due-time decisions use PostgreSQL's clock; keep the database host's clock
correct. Polling and queue load affect when execution actually begins.

See the [CLI examples](scheduling-cli.md), [upgrade guide](scheduling-upgrade.md),
and [reliability contract](reliability.md).
