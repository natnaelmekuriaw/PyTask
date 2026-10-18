# Reliability contract

PyTask uses at-least-once execution with a finite attempt budget. A task can run
again after a handler failure, timeout, or expired worker lease. It stops when
an attempt succeeds or its budget is exhausted. Submission defaults to three
total attempts, a 300-second execution deadline, and retry delays capped at
60 seconds. Set `max_attempts=1` to disable retries.

## Ownership and recovery

Claiming locks one eligible pending task, assigns a fresh UUID token, creates
its attempt record, and commits before the handler starts. The lease deadline
uses PostgreSQL's clock. Workers renew a 30-second lease every 10 seconds by
default. Renewal and completion require the current token and a live lease.
An expired lease cannot be revived.

Each worker recovers a bounded batch of expired leases before claiming work.
Recovery locks rows with `SKIP LOCKED`, marks the interrupted attempt abandoned,
and either schedules another attempt or fails the task permanently. The next
attempt gets a new token even if the same worker ID is reused. An old worker
cannot renew or finish that new attempt.

If renewal fails or stalls, the parent cancels the child process. A separate
watchdog enforces a conservative local deadline while the renewal call is
blocked. Database lock and statement timeouts bound lease maintenance queries.
The worker exits after losing its claim; another worker can recover it once
the database lease expires.

## Retries and deadlines

After failed attempt `n`, the retry delay is chosen uniformly from zero to
`min(retry_max_seconds, retry_base_seconds * 2 ** (n - 1))`. Eligibility uses
`available_at`, so workers cannot claim a retry before it is due. Timeouts and
process crashes consume an attempt just as handler exceptions do.

The execution deadline covers process startup, handler execution, and process
exit. On timeout, the parent terminates the child and uses a kill fallback if
necessary. It reaps the process before recording the timeout. Termination does
not guarantee handler cleanup runs, and does not stop subprocesses created by
the handler. Handlers should manage their own external resources.

Ctrl+C or SIGTERM stops new claims and lets the active attempt finish within
its configured deadline. Its lease continues to renew during that shutdown.

## Idempotency

A handler may complete an external side effect and crash before its result is
stored. Recovery can then run it again. An expired worker can also overlap a
new attempt before it observes cancellation. Claim tokens protect PyTask's
database updates; they do not fence writes to other systems.

Give each operation a stable business identifier in its arguments. For example,
an invoice handler can use a unique invoice ID in the same database transaction
as its write, or pass that ID as an idempotency key to a payment API. A repeated
call should return the existing result rather than repeat the side effect.

## History

`status TASK_ID` shows the current state, attempt budget, next eligible time,
lease deadline, and last error. `attempts TASK_ID` returns every attempt in
number order with its worker, start and finish times, outcome, and error.
Attempt outcomes are `running`, `succeeded`, `failed`, `timed_out`, or
`abandoned`. A task can be `pending` while its last attempt is `failed`.
