# Iteration 012 — Phase 3B staging identity and isolation proof

## Goal

Prove identity, tenant, conversation, student-memory, prompt-log and owner-evidence isolation using
synthetic data only, while defining reviewable staging database and admin contracts.

## Baseline

- Ruff: pass
- mypy strict: pass, 55 source files
- pytest: 126 passed
- TypeScript strict: pass

## Implementation

- Added verified external identity assertions and data-minimized effective user IDs.
- Added a synthetic-only in-memory proof store with hard owner/student evidence separation.
- Added a hash-pinned, governance-aware candidate persona loader.
- Added PostgreSQL 15+ up/down migrations under `xiewenxian_staging`.
- Added four immutable GET-only admin contracts.
- Added 41 focused Phase 3B tests, including PostgreSQL AST parsing in CI.

## Validation so far

- Focused tests: 41 passed.
- Full pytest: 167 passed.
- Ruff: pass.
- mypy strict: pass, 63 source files.
- TypeScript strict: pass.
- PostgreSQL AST parse: pass, two migration files.
- External DB calls: 0.
- Real identities/data: 0.
- Production/provider calls: 0.

Decision: `LOCAL_ACCEPTANCE_COMPLETE_GITHUB_PENDING`

Required stop: `NEEDS_HUMAN_PHASE_3B_REVIEW`.
