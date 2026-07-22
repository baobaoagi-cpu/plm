# Decision 0005 — Gate DB-1 uses a disposable, network-disabled PostgreSQL server

- Status: accepted
- Date: 2026-07-21
- Authority: explicit human approval for `Gate DB-1 — Local PostgreSQL RLS Execution Proof`

## Decision

Run the existing Phase 3B schema only against an official PostgreSQL 15 container with no network,
no host port, tmpfs storage and synthetic identities. Create separate owner, app and admin-readonly
roles without login, superuser or `BYPASSRLS` capability.

The execution harness must apply the migration twice, exercise RLS through the provider roles,
prove the rollback guard, perform the approved staging rollback, and always delete the container.

## Finding

Real execution exposed a rerun failure hidden by AST and contract tests. The migration now uses a
transaction-local tenant setting, making its fixed tenant seed compatible with already-forced RLS.

## Boundary

The custom PostgreSQL settings are trusted server-side database context, not client authentication.
No external staging or production identity is authorized by this proof.

## Stop

`NEEDS_HUMAN_GATE_DB1_REVIEW`
