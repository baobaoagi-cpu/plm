# Current Milestone Plan

## Milestone

`Gate DB-1 — Local PostgreSQL RLS Execution Proof`

## Goal

Execute the existing Phase 3B migration on a disposable real PostgreSQL 15 server and prove forced
RLS, synthetic identity isolation, data-class separation, least-privilege roles and guarded
rollback without any external database or production connection.

## Delivered locally

- Reproducible PowerShell runner using an official PostgreSQL 15 image.
- Network-disabled container, no host port, tmpfs data and unconditional cleanup.
- Three fail-closed provider roles and synthetic owner/student A/student B identities.
- Fifteen executable RLS/data-class assertions and four migration/role/rollback checks.
- Migration rerun defect repaired with transaction-local staging tenant context.
- Static regression assertion plus machine-readable evidence and acceptance records.

## Verified

- PostgreSQL 15.18 migration applied twice in one fresh database.
- Student A/B conversations, memories and prompt logs remained isolated.
- Owner Evidence and Student Memory rejected cross-class writes.
- Missing context failed closed; forced RLS constrained the table owner.
- Admin-readonly could read its selected scope and could not write.
- Unguarded rollback was rejected without changes; guarded staging rollback removed the schema.
- Disposable container and all synthetic rows were removed.

## Pending human action

- Human Gate DB-1 review.

## Explicitly not delivered

- External staging database, persistence adapter or connection-pool context lifecycle.
- Real LINE/Partner identity, owner/student data, Mem0, R2 or admin UI.
- Formal MiniMaxTTSService, Pipecat Pipeline, LINE activation or LiveKit integration.
- Phase 3D, Task 005, release persona or production deployment.

## Required stop

`NEEDS_HUMAN_GATE_DB1_REVIEW`
