# Phase 3B — Staging Identity and Data-Isolation Proof

Status: `COMPLETED / NEEDS_HUMAN_PHASE_3B_REVIEW`

## Goal

Prove, with synthetic data only, that Xie Wenxian staging identities, conversations, student
memory, prompt logs and owner evidence cannot cross principal or data-class boundaries.

## Fixed boundaries

- Tenant: `xie_wenxian`
- Environment: staging only
- Persona source: governed candidate register, not a release persona
- External identity: a LINE/Partner adapter must verify first; mapping never trusts a client ID
- Effective identity: stable SHA-256-derived ID; raw external IDs are not logged or persisted
- Database target: provider-neutral PostgreSQL 15+ migration under `xiewenxian_staging`
- Database execution: not authorized in this phase without a separately confirmed staging DB
- Secrets: environment variables or a persona-specific Secret Manager only; no values in Git
- Pipecat remains the sole orchestrator; Generation Guard is unchanged

## Data classes

| Class | Principal scope | Phase 3B persistence rule |
|---|---|---|
| Conversation | exact tenant + effective user | synthetic digest only |
| Student memory | student only | origin must be `student_conversation` |
| Prompt log | exact tenant + effective user | prompt digest only |
| Owner evidence | verified owner only | remains `OWNER_PROVIDED_UNREVIEWED` |

Owner evidence cannot enter the student-memory table in either the Python proof store or the
PostgreSQL schema. Composite foreign keys bind each row to tenant, principal and principal kind.
RLS is enabled and forced on every table.

## Read-only admin contracts

Only four immutable contracts are allowed:

- `/` — Control Tower truth snapshot
- `/data-map` — schema and isolation topology
- `/persona` — candidate governance state
- `/soul-foundry` — candidate/review summary

All use `GET`, expose no mutation method, report production disconnected and cannot publish.
This milestone does not build an admin UI or HTTP server.

## Acceptance

- Unverified LINE/Partner identity fails closed.
- Two synthetic students receive distinct effective IDs.
- Conversation, student memory and prompt log A/B reads never cross.
- Student or governor cannot submit owner evidence.
- Owner evidence cannot be written to student memory.
- Candidate loader rejects wrong hash, wrong persona, owner quotes or runtime eligibility.
- Migration contains tenant constraints, composite foreign keys, forced RLS, indexed FKs,
  provider-role guards, least-privilege grants and a staging-only rollback guard.
- Four read-only admin contracts report only evidence-backed staging state.
- Ruff, mypy strict, full pytest, TypeScript strict, secret scan and forbidden-import checks pass.

## Stop

`NEEDS_HUMAN_PHASE_3B_REVIEW`

No production deployment, real user data, Mem0 write, LINE delivery, public voice or release persona
is authorized.
