# Runtime image

The Dockerfile builds wheels with runtime constraints in a build stage and
installs them into `/opt/venv`. The final stage receives that environment,
Alembic configuration, migration scripts, and the license. Build wheels,
development tools, tests, and host virtual environments stay outside it.
Docker's [multi-stage build guide](https://docs.docker.com/build/building/multi-stage/)
describes this separation.

The base is `python:3.12-slim-bookworm`. A build argument can select an
equivalent Python 3.12 image by immutable digest. Build and runtime stages
must use the same compatible base. Runtime dependency pins live in
[constraints](../constraints/README.md); a mutable base tag and build backend
mean this is not a bit-for-bit reproducibility guarantee.

The final process runs as UID/GID 10001. Application files belong to root.
Bytecode writes are disabled, and stdout is unbuffered. Compose supplies a
read-only root filesystem and a bounded temporary directory. Task handlers
that need durable files must use an explicitly designed storage mount;
`/tmp` contents are disposable.

## Entry points

| Command after the image name | Behavior |
| --- | --- |
| `api` | Check registry and schema, then replace the launcher with Uvicorn |
| `worker` | Check registry and schema, then run the continuous worker |
| `scheduler` | Check schema, then run the scheduler without a registry |
| `migrate` | Explicitly execute Alembic upgrade to head |
| `cli ...` | Forward literal arguments to the existing CLI |
| `check` | Check database revision and mapped columns without writes |
| `probe api` | Read loopback API readiness with a bounded response |
| `probe database` | Check database/schema dependency readiness |

`api` is the default command. Help requires no configuration. The launcher
uses the current interpreter and `exec`, with no shell wrapper. Compose's init
process forwards termination and reaps orphaned processes. Health checks are
configured per role in Compose because one image serves several processes.

The installed package license uses the SPDX MIT expression and explicitly
includes LICENSE. This metadata requires setuptools 77 or newer; see the
[setuptools packaging reference](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html).

CI builds the runtime image, checks its entry point under a read-only root,
and verifies the unprivileged identity and packaged migration history.
It does not publish an image. Record a built image digest when making a release.
