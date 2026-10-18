# Crash recovery demonstration

Use a disposable local PostgreSQL database configured as described in the
[upgrade guide](monitoring-upgrade.md).

Run the process recovery scenario:

```powershell
.\.venv\Scripts\pytest -vv tests/worker/test_process_recovery.py
```

The test creates a separate database schema and performs this sequence:

1. Submit a registered addition task.
2. Start a child worker that commits a claim and exits with code 7.
3. Confirm the child has exited, then expire its stored lease.
4. Read monitoring data and verify one expired running task.
5. Start a replacement worker, recover the lease, and execute the retry.
6. Verify a succeeded task and an abandoned first attempt.
7. Verify monitoring reports one recovered abandonment, one success, one
   retry start, one execution sample, and two queue wait samples.

Lease expiry is moved directly in the test database so the demonstration does
not wait for a production-length lease. The process death is real. The child
dies after claiming and before handler execution; this scenario does not
simulate every possible point of failure.

The test cleans up its schema and child process. Its rows are isolated from
normal CLI and API monitoring reads. The assertions verify snapshots inside
that schema. This is a reproducible correctness example, not a throughput
benchmark.

The replacement worker's success does not provide exactly-once execution.
A handler can perform a side effect before its worker dies, so application
idempotency remains necessary. See the [delivery contract](reliability.md).
