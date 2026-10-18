# Worker design

Each worker runs one task at a time. Running more worker processes increases
parallelism without sharing Python state between task handlers.

## Claim transaction

The worker selects an eligible pending row using `FOR UPDATE SKIP LOCKED`.
Eligibility requires `available_at` to have passed and an unused attempt in the
task's budget. Rows are ordered by availability, creation time, and ID. A
competing worker skips a locked row and can claim another.

Claiming marks the task running, increments its attempt count, assigns a fresh
claim token, and creates a running attempt record. The task and attempt share
that token. The lease expiry and start time use PostgreSQL's clock. All these
writes commit together before the handler starts, so user code never holds a
claim transaction open.

## Task process

The parent starts a fresh Python process using the `spawn` start method. It
passes the registered task name and JSON arguments; the child imports the
configured registry and calls the handler. Database connections and handler
objects are not sent to the child. The child returns a bounded JSON result or
an error through a pipe. An exit without a message becomes a failed outcome.

The parent enforces the task's execution deadline through process startup,
execution, and exit. A returned result does not bypass the deadline if child
threads keep the process alive. Timeout and lease loss both stop and reap the
child, with a kill fallback when termination does not finish it.

## Lease maintenance

A parent thread renews the lease in separate, short database transactions.
Renewal requires the task ID, worker ID, current claim token, running state,
and an unexpired lease. A separate watchdog cancels execution if the local
lease deadline passes while renewal is blocked. The local deadline uses a
monotonic clock and is conservative about database round trips.

An idle worker recovers a bounded batch of expired leases before claiming its
next task. Recovery also uses `FOR UPDATE SKIP LOCKED`. It closes the interrupted
attempt as abandoned and either makes the task pending after backoff or marks
it failed when the attempt budget is exhausted. Recovery never increments the
attempt count; the next claim does that.

## Finalization

The parent locks the task and verifies its running state, worker ID, claim
token, and lease expiry before writing. A stale worker cannot finish a newer
attempt, even when both processes use the same worker ID.

Finalization closes the attempt and updates the task in one transaction.
Success stores the result and finish time. Failure or timeout stores the error
and schedules a retry with exponential backoff and full jitter, unless the
attempt budget is exhausted. Terminal tasks clear their lease and token.

`status` shows the current task record; `attempts` shows individual execution
records in number order. Each attempt retains its own timestamps and error
after a task is retried.

## Shutdown and delivery

Ctrl+C or SIGTERM stops new claims. The parent continues renewing the current
lease while the attempt finishes within its execution deadline. If the parent
dies, a later worker recovers its expired lease.

Handlers must tolerate repeated execution. A side effect can succeed before a
worker loses its lease or stores its result. See the [reliability contract](reliability.md)
for the delivery guarantees, idempotency guidance, and process cleanup limits.
