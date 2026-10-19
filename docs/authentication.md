# API authentication

The API requires an operator-issued bearer key by default. Each credential
grants explicit permissions across the shared queue. Health probes remain
public. Command-line database access keeps its existing PostgreSQL privileges.

Start with the [upgrade procedure](authentication-upgrade.md) for an existing
deployment, or [key generation](authentication-keys.md) for a new one.

## Guides

- [Configuration](authentication-configuration.md)
- [Permissions](authentication-permissions.md)
- [Key generation and rotation](authentication-keys.md)
- [Container setup](authentication-deployment.md)
- [PowerShell requests](authentication-examples.md)
- [Acceptance checks](authentication-verification.md)
- [Troubleshooting](authentication-troubleshooting.md)
- [Design](authentication-design.md)

## Boundaries

Keys authenticate services and operators. There are no user accounts, login
sessions, automatic token expiry, or tenant ownership rules. Read permissions
can expose arguments, results, and error history for every retained task.
A schedule manager can arrange future execution without task submission access.

Use TLS at a trusted ingress for access beyond localhost. Restrict network
access to PostgreSQL separately. Protect key files, client logs, proxy logs,
and terminal transcripts. The application does not implement request quotas
or distributed rate limiting.

Keys are loaded at startup. Removing a manifest record revokes it only after
every API process is recreated. See [rotation](authentication-keys.md).

