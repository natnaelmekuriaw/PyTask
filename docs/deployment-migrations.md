# Database migrations in deployment

API, worker, and scheduler startup compare the database's Alembic heads with
the scripts packaged in the image. The sets must match exactly. Startup also
checks mapped table columns using zero-row reads. It never creates a version
table, stamps revisions, or executes upgrade functions.

The preflight transaction is read only, with a two-second lock timeout and
five-second statement timeout. Its engine is disposed before the launcher
replaces itself with the service process. A matching revision stamp does not
hide a missing mapped column. It does not prove every database invariant or
index is intact; retain Alembic model comparison in the upgrade process.

## Apply changes

Stop API, workers, and schedulers and take a backup before an upgrade affecting
stored data. Use the exact image intended for the application services.
Run one migration operator at a time.

```powershell
docker compose --profile runtime stop api worker scheduler
```

```powershell
docker compose --profile tools run --rm migrate
```

The migration service executes `python -m alembic -c /app/alembic.ini upgrade head`.
It does not import the task registry. Its restart policy is disabled.

Check the resulting image/schema combination:

```powershell
docker compose --profile tools run --rm ops check
```

For a model comparison, invoke Alembic explicitly in the migration image:

```powershell
docker compose --profile tools run --rm --entrypoint python migrate -m alembic -c /app/alembic.ini check
```

After successful checks, start the application using the built image. If
startup reports an incompatible revision, confirm that all services and the
migration command reference the same image and database. A database newer
than an old image also fails this check; do not bypass it by changing stamps.

No migration is added by deployment setup. An existing monitoring database
at revision `20261019_07` remains at that revision.
