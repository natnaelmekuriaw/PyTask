# File-based credentials

The application accepts either `PYTASK_DATABASE_URL` or
`PYTASK_DATABASE_URL_FILE`. Supplying both nonempty values is an error.
Secret files must be regular, readable UTF-8 files of at most 8192 bytes;
a UTF-8 BOM and trailing whitespace are accepted. Errors identify the setting
without echoing file contents or credential paths.

For Compose, `compose.secrets.yaml` mounts application and PostgreSQL
credential files. Create `.secrets/database-url.txt` containing the complete
container URL and `.secrets/postgres-password.txt` containing its matching
database password. These files and the directory are ignored by Git and
excluded from the application image build context.

For the unchanged local development credentials, the files contain:

- URL: `postgresql+psycopg://pytask:pytask@postgres:5432/pytask`
- Password: `pytask`

Use your actual credentials for another database. The application file must
be readable by container UID 10001. Compose's local file-backed secrets are
mounts, not an encrypted secret store. File ownership options are limited
with file sources; see [Docker's secrets guide](https://docs.docker.com/compose/how-tos/use-secrets/).

Validate the combined definition after creating the files:

```powershell
docker compose -f compose.yaml -f compose.secrets.yaml --profile runtime --profile tools config --quiet
```

Use both files consistently for migration and runtime commands:

```powershell
docker compose -f compose.yaml -f compose.secrets.yaml --profile tools run --rm migrate
```

```powershell
docker compose -f compose.yaml -f compose.secrets.yaml --profile runtime up -d --no-build
```

The overlay explicitly empties direct URL/password values and mounts the file
alternatives. Host environment URL values are not copied into the container.

Changing PostgreSQL's initialization password file does not change a password
already stored in an existing database volume. Rotate the database credential
through PostgreSQL administration, update the application URL file, and
recreate affected services together. Do not remove the data volume to rotate
credentials. No automatic rotation or secret-file watching is implemented.
