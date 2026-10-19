# Generate and manage API keys

Run commands separately from the repository root. These commands work without
Docker, PostgreSQL, a task registry, or database environment variables.

Create the ignored local directory:

```powershell
New-Item -ItemType Directory -Force .secrets | Out-Null
```

Generate a task producer key and its verification manifest:

```powershell
.\.venv\Scripts\python -m pytask_service.auth generate --id producer --scope tasks:submit --token-file .secrets/producer-token.txt --manifest .secrets/api-keys.json
```

Repeat `--scope` to grant additional permissions from the
[matrix](authentication-permissions.md). Each output path must be new and its
parent directory must exist. Generation refuses to overwrite existing files.
If creating the manifest fails, the new token file is removed where possible.

The token file contains the usable credential. Share it only with its client.
The API needs the manifest, which contains the digest and permissions.
Inspection shows IDs and permissions without tokens or digests:

```powershell
.\.venv\Scripts\python -m pytask_service.auth inspect --manifest .secrets/api-keys.json
```

New files request mode 0600 on POSIX. On Windows, check directory and file ACLs
before sharing a machine. Keep both files out of source control, build contexts,
logs, and shell arguments.

## Rotation and revocation

1. Generate a replacement with a new ID into separate new files.
2. Combine the two manifests' `keys` arrays under one `version: 1` object.
3. Validate the combined manifest using `inspect`.
4. Replace the configured manifest and recreate every API process.
5. Give the new token to its client and verify the intended operations.
6. Remove the old record, validate again, and recreate every API process.
7. Verify the old token returns 401 on every instance, then retire its file.

Replacing a mounted file alone does not update a running process. Tokens have
no built-in expiry. Emergency revocation requires removing the record and
recreating all API instances; isolate the ingress while doing so if necessary.

