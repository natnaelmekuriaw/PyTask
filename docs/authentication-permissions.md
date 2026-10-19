# API permissions

Grant only the operations each client needs. Permissions do not imply one
another, and wildcard grants are unsupported.

| Operation | Required permission |
| --- | --- |
| Submit a task | `tasks:submit` |
| List tasks, inspect a task, read attempts | `tasks:read` |
| List and inspect schedules | `schedules:read` |
| Create, pause, or resume schedules | `schedules:write` |
| List tasks belonging to a schedule | `schedules:read` and `tasks:read` |
| Read monitoring statistics | `monitoring:read` |
| Download enabled OpenAPI JSON | `docs:read` |
| GET health liveness and readiness | Public |

Successful create and control operations return their normal resource response;
write access therefore includes that operation's response data. A producer can
receive its submitted task ID without permission to list other tasks. Schedule
write access can execute registered tasks through future dispatches.

Read grants cover all records in this deployment. There is no owner field
checked against key IDs. Key IDs identify clients for audit correlation and
do not partition data.

OpenAPI declares HTTP bearer authentication and lists permissions per operation,
including an `x-required-scopes` list. These are application permissions;
there is no OAuth authorization or token-exchange endpoint.

A valid credential with missing permissions receives 403 and
`insufficient_scope`. Authentication failures receive 401. See the
[HTTP examples](authentication-examples.md).

