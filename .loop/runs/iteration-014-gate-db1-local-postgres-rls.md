# Iteration 014 — Gate DB-1 local PostgreSQL RLS execution

## Single goal

Execute the Phase 3B migration and its isolation rules on real local PostgreSQL, using synthetic
data only and without any external connection.

## Execution

- PostgreSQL: 15.18, official `postgres:15-alpine` image.
- Isolation: Docker network `none`, no published port, tmpfs database storage.
- Roles: migration owner, app, admin-readonly; all non-login/non-superuser/non-`BYPASSRLS`.
- Migration applications: 2 in the same fresh database.
- RLS/data-class behaviors: 15 passed.
- Total gate checks: 19 passed.
- Final clean gate elapsed time: 3,373 ms.
- Cleanup: disposable container and all synthetic rows removed.

## Red/green record

1. First real run: first migration apply passed; second apply failed because forced RLS rejected
   the tenant seed without tenant context.
2. Migration repaired with transaction-local `app.current_tenant_id`; static regression added.
3. Second run: migration and all RLS checks passed; runner incorrectly treated the intentionally
   rejected unguarded rollback as a fatal harness error.
4. Runner repaired to assert the expected non-zero rollback result.
5. Third fresh run: all 19 checks and cleanup passed.

No acceptance requirement was changed and no product failure was hidden.

## External effects

- External database/provider/LINE/LiveKit/Mem0/R2/production connections: 0.
- Real identities, transcripts, memories, evidence or audio: 0.
- Paid API cost: USD 0.00.

## Full regression

- Ruff: pass.
- mypy strict: pass, 79 files.
- pytest: pass, 232 tests.
- TypeScript strict: pass.
- npm dependency tree: pass.
- JSON, Git diff, high-confidence secret and forbidden-runtime scans: pass.
- Python validation elapsed: 19,846 ms.

Decision: `NEEDS_HUMAN_GATE_DB1_REVIEW`.
