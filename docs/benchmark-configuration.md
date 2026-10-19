# Benchmark configuration

The [verification script](benchmarks.md) runs the default benchmark suite
when passed `-Benchmarks`. These options customize that step:

| Script option | Default | Meaning |
| --- | --- | --- |
| `-BenchmarkTasks` | 20 | Measured tasks in each case |
| `-BenchmarkWorkers` | 1, 2, 4 | Distinct worker counts |
| `-BenchmarkRepeat` | 3 | Repetitions per workload and worker count |
| `-BenchmarkWarmup` | 2 | Unmeasured tasks in each case |
| `-BenchmarkTimeoutSeconds` | 120 | Startup, warmup and measurement phase budget in seconds |
| `-BenchmarkOutput` | benchmark-results | Parent for unique report directories |

`-SkipInstall` and `-SkipBuild` reuse an existing installation and image;
omit them after dependency or image changes. Other verifier options,
including `-DatabaseUrl`, retain their existing behavior.

A smaller functional check, with every verification step still enabled:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -Benchmarks -BenchmarkTasks 3 -BenchmarkRepeat 1
```

PowerShell array arguments such as `-BenchmarkWorkers 1,2,4` are best passed
when invoking the script directly from PowerShell. The default array needs
no extra argument when using `powershell.exe -File`.

## Direct module options

After setup, the benchmark module also runs independently:

```powershell
.\.venv\Scripts\python.exe -m pytask_service.benchmarks --help
```

Independent runs require `PYTASK_DATABASE_URL` or its existing secret-file
equivalent. They do not stop existing application containers, install
dependencies, apply migrations or run acceptance checks.

The module adds `--workloads noop sleep checksum`, `--sleep-ms 20`,
`--iterations 10000`, `--task-timeout 10`, `--poll-interval 0.05` and
`--no-recovery`. These defaults are recorded in every JSON report.
Changing workload cost changes what is being compared.

## Limits

Task count is 1–10000, repetitions 1–10, warmup 0–1000 and worker counts
1–32, with at most eight distinct counts. Workloads and counts cannot
repeat. A plan is limited to 100000 tasks including warmup across all cases.

Case timeout is 5–3600 seconds, handler timeout 1–120 seconds and completion
polling 0.01–1 second. Sleep cost is 0–1000 milliseconds; checksum cost is
1–1000000 rounds. Invalid or nonfinite values fail before database work.

Warmup tasks share the queue. They do not guarantee that every worker has
executed a handler. Phase timeouts are checked between bounded operations;
they are not a hard wall-clock limit on the whole command. Schema setup,
reference result preparation, report writing and shutdown add elapsed time.

A database user must be able to create and drop schemas. Use a local or
disposable database. Isolation keeps benchmark rows separate while all
schemas still share server CPU, storage, connections and other resources.
