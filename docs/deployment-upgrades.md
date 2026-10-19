# Upgrades and rollback

Use one reviewed image for the API, workers, scheduler, and migration command.
Record the current image identity, application configuration, and database
revision before replacing a running deployment.

For the local mutable image tag, retain an explicit reference before rebuilding:

```powershell
docker image tag pytask:local pytask:before-upgrade
```

Stop application services using their configured grace periods:

```powershell
docker compose -f compose.yaml -f compose.auth.yaml --profile runtime stop api worker scheduler
```

Take a [database backup](deployment-backups.md), build the new image, run the
explicit migration service, and check its schema. Recreate application services
using that image only after those steps succeed.

A rollback has two parts: image compatibility and database compatibility.
If the new release changed no schema, an earlier compatible image can be
selected through `PYTASK_IMAGE` and used with `up --no-build`. Confirm its
startup check accepts the stored revision.

If a release changed schema, replacing the image alone can fail or interpret
data incorrectly. Review the migration's downgrade behavior and data loss
implications, or restore a verified backup into an isolated database for
cutover. Do not edit the version table to make an old image appear compatible.

Retain the previous image and backup until the new deployment has completed
representative task execution, scheduling, monitoring, and shutdown checks.
A health response alone is insufficient to decide an upgrade succeeded.

Keep the authentication overlay and reviewed manifest in every runtime
recreation command. Include the database secret overlay as well when used.
Apply the [authentication upgrade](authentication-upgrade.md) before replacing
an unauthenticated API. No database revision is added for authentication.

An earlier image may lack authentication even when its database schema is
compatible. Restrict ingress before rolling back, and verify anonymous
requests remain denied before restoring traffic. Credential changes require
recreating every API instance; editing a mounted file does not hot-reload keys.

This stage defines local packaging and operating procedures. It does not
publish images, create release tags, or perform an automatic deployment.
