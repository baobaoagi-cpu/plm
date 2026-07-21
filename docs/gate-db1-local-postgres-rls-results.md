# Gate DB-1 — Local PostgreSQL RLS Results

Status: `COMPLETED / NEEDS_HUMAN_GATE_DB1_REVIEW`

## Outcome

The Phase 3B schema was executed on PostgreSQL 15.18 in a disposable, network-disabled local
container. The final clean run passed 19 checks: 15 RLS/data-class behaviors plus migration
idempotency, role attributes, rollback refusal and approved rollback.

| Requirement | Result |
|---|---|
| Real PostgreSQL 15+ execution | VERIFIED — 15.18 |
| External network/database use | VERIFIED NONE — container network `none` |
| Synthetic-only data | VERIFIED |
| Migration first apply | VERIFIED |
| Migration second apply under forced RLS | VERIFIED after defect repair |
| Student A/B conversation isolation | VERIFIED |
| Student A/B memory isolation | VERIFIED |
| Student A/B prompt-log isolation | VERIFIED |
| Cross-effective-user write rejection | VERIFIED |
| Owner Evidence → Student Memory rejection | VERIFIED |
| Student → Owner Evidence rejection | VERIFIED |
| Missing identity context fail-closed | VERIFIED |
| Table owner constrained by forced RLS | VERIFIED |
| Admin-readonly cannot write | VERIFIED |
| Provider roles non-login/non-superuser/no-BYPASSRLS | VERIFIED |
| Rollback without staging guard | VERIFIED REJECTED, schema retained |
| Rollback with staging guard | VERIFIED, schema removed |
| Container/data cleanup | VERIFIED |

## Defect found and repaired

The original migration succeeded once but was not rerunnable after forced RLS became active. Its
tenant seed statement lacked RLS tenant context on the second run. The migration now sets
`app.current_tenant_id=xie_wenxian` with transaction-local scope before schema work. A static
regression assertion and the twice-applied real PostgreSQL harness protect this behavior.

No acceptance threshold was weakened.

## Evidence

- Runner: `scripts/run_gate_db1.ps1`
- SQL proof: `tests/integration/gate_db1_rls_proof.sql`
- Machine-readable record: `.loop/evidence/gate-db1-local-postgres-rls-i14.json`
- Iteration record: `.loop/runs/iteration-014-gate-db1-local-postgres-rls.md`

## Remaining boundary

This verifies PostgreSQL enforcement when trusted server code supplies the effective identity
context. It does not authorize or prove an external staging database, connection-pool reset logic,
real LINE/Partner identity, admin UI, Mem0, production or deployment.

Required stop: `NEEDS_HUMAN_GATE_DB1_REVIEW`.
