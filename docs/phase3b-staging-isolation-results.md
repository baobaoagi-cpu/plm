# Phase 3B Staging Identity and Data-Isolation Results

Status: `LOCAL_ACCEPTANCE_COMPLETE / GITHUB_ACTIONS_PENDING`

## Verified locally

| Requirement | Result | Evidence |
|---|---|---|
| Xie Wenxian staging tenant only | VERIFIED | mapper/store rejection tests |
| Unverified LINE／Partner identity denied | VERIFIED | identity mapping tests |
| Raw external ID excluded from effective ID/admin summary | VERIFIED | identity mapping tests |
| Synthetic students A/B conversations isolated | VERIFIED | bidirectional access tests |
| Synthetic students A/B memory isolated | VERIFIED | per-principal list tests |
| Synthetic students A/B prompt logs isolated | VERIFIED | per-principal list tests |
| Owner Evidence accepted only from OWNER | VERIFIED | role rejection tests |
| Owner Evidence cannot enter Student Memory | VERIFIED | Python and SQL contract tests |
| Candidate persona wrong hash/state fails closed | VERIFIED | loader mutation tests |
| Four admin contracts are GET-only | VERIFIED | immutable contract tests |
| PostgreSQL migration parses | VERIFIED | pglast AST parse, up/down |
| PostgreSQL migration applied to external DB | UNKNOWN / NOT EXECUTED | no approved DB identity |

## Database contract

The migration creates only `xiewenxian_staging` tables for tenants, principals, conversations,
student memory, prompt logs and owner evidence. It uses composite foreign keys, forced RLS,
least-privilege conditional grants and a rollback guard that refuses non-staging execution.

No PostgreSQL server, Cloud SQL, Supabase project, Mem0, R2, LINE OA or production service was
contacted. SQL parse and contract evidence must not be described as a live database smoke test.

## Admin contract

`/`, `/data-map`, `/persona` and `/soul-foundry` return immutable evidence snapshots. They report
production disconnected, no release persona and publishing disabled. No HTTP server or UI was
created in Phase 3B.

## Architecture preservation

- Pipecat remains the sole orchestrator.
- Generation Guard was not modified.
- No Tracy or legacy runtime import exists.
- No MiniMax service, connection pool, LiveKit Agent, Mem0 or production adapter was added.

## Stop

After final validation and publication, stop at `NEEDS_HUMAN_PHASE_3B_REVIEW`.
