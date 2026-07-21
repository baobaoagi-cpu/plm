# Gate DB-1 — Local PostgreSQL RLS Execution Proof

Status: `COMPLETED / NEEDS_HUMAN_GATE_DB1_REVIEW`

## Goal

Execute the Phase 3B migration against a real, disposable PostgreSQL 15 server and prove the
tenant, principal, data-class, role and rollback boundaries with synthetic data only.

## Fixed execution boundary

- Official `postgres:15-alpine` image pinned by digest in the evidence record.
- Disposable container with `--network none`; no host port and no external database connection.
- Database storage is tmpfs and the container is removed after every run.
- All identities, content and digests are synthetic; no raw LINE, Partner, owner or student data.
- Three non-login, non-superuser, non-`BYPASSRLS` roles: migration owner, app and admin-readonly.
- No provider, Mem0, R2, LINE, LiveKit, voice or production connection.

## Acceptance

- The up migration applies twice after forced RLS is active.
- All six tables have enabled and forced RLS.
- Student A and B cannot read each other's conversation, memory or prompt-log rows.
- A principal cannot write a row for another effective user.
- Owner Evidence is visible and writable only in owner scope.
- Owner Evidence cannot enter Student Memory, and a student cannot enter Owner Evidence.
- Missing identity context returns no principal rows.
- Forced RLS constrains the table owner.
- The admin role can read only the selected RLS scope and cannot write.
- All provider roles remain non-login, non-superuser and non-`BYPASSRLS`.
- Rollback fails without `app.environment=staging`, changes nothing when refused, and succeeds with
  the explicit staging guard.

## Trust boundary retained

RLS trusts transaction/session context set by the application database boundary. This proof does
not claim that PostgreSQL authenticates LINE or Partner identities. A future database adapter must
derive `app.current_tenant_id` and `app.current_effective_user_id` from the already verified
server-side principal and reset both values on every transaction; client-supplied values remain
forbidden.

## Stop

`NEEDS_HUMAN_GATE_DB1_REVIEW`

External staging databases, production, real identities/data and Phase 3D remain unauthorized.
