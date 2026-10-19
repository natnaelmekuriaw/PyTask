# Benchmarks

From the repository root, with the project virtual environment present and
Docker Desktop running in Linux container mode:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -Benchmarks
```

This is the full local acceptance command. It installs dependencies, reuses
or creates local API key files, builds the image, starts PostgreSQL, applies
migrations, checks migration drift, runs lint, formatting, type checks and
the full test suite, then runs the benchmarks. It finally starts the API,
worker and scheduler and checks authenticated example task execution.

Application containers stay stopped during tests and benchmarks. PostgreSQL
stays running. A failure stops the sequence immediately; services are not
automatically restarted after failed checks. The script restores its process
environment and working directory. It does not push commits or publish images.

## What runs

The default plan has three workloads, worker counts of 1, 2 and 4, and three
repetitions: 27 cases, 540 measured tasks and 54 warmup tasks. Each case gets
a fresh schema and worker group. A separate recovery check crashes one
worker after claiming a task and waits for natural lease expiry.

The measurements use host virtual-environment Python and the configured
PostgreSQL server. Each task uses the production worker's fresh handler
process. The suite measures engine completion and queue timing; it does
not measure HTTP throughput, API authentication, recurring dispatch or
Docker worker throughput.

Expect substantial process startup work, especially on Windows. Progress
prints once per case. The report records observed results without a
hardware-dependent pass threshold. Success requires correct task results,
complete attempt history and successful cleanup.

## Output and review

The final benchmark JSON line names a new directory beneath
`benchmark-results/`. Open `results.md` for the tables and keep
`results.json` and `results.csv` with it. Generated runs are ignored by Git.
No measured results are checked into the repository.

Review the complete run status, each case, repetition ranges and recovery
outcomes before publishing a performance claim. A successful tiny smoke run
establishes functionality; larger repeated runs are needed for comparisons.

See [configuration](benchmark-configuration.md),
[measurement design](benchmark-design.md), [report formats](benchmark-results.md),
[recovery](benchmark-recovery.md) and [troubleshooting](benchmark-troubleshooting.md).
