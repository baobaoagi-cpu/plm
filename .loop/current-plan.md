# Current Milestone Plan

## Milestone

`Phase 3B — Staging Identity and Data-Isolation Proof`

## Goal

Prove with synthetic data that Xie Wenxian staging identities, conversations, student memory,
prompt logs and owner evidence cannot cross tenant, principal or data-class boundaries.

## Delivered locally

- Verified LINE／Partner／synthetic assertion to hashed `effective_user_id` mapping.
- Xie Wenxian-only staging tenant and principal kinds.
- Synthetic-only conversation, student-memory, prompt-log and owner-evidence proof store.
- Fail-closed candidate persona loader pinned to the governed register hash.
- PostgreSQL 15+ up/down migration contracts with forced RLS and provider-role guards.
- Four immutable GET-only admin contracts: `/`, `/data-map`, `/persona`, `/soul-foundry`.
- Forty-one Phase 3B tests plus the full regression suite.

## Validation complete

- Secret, real-identity, forbidden-import, Tracy-contamination and Git-diff scans passed.
- Durable evidence hashes and iteration record are committed.
- Phase 3B branch and Draft PR #2 are published; GitHub Actions passed.

## Pending human action

- Human Phase 3B review.

## Explicitly not delivered

- External DB migration execution or persistence adapter.
- Real LINE／Partner verification, real user identity, Mem0, R2 or audio.
- Admin HTTP server or UI.
- Release persona, production, Task 005, Pipecat pipeline or LiveKit.

## Required stop

`NEEDS_HUMAN_PHASE_3B_REVIEW`
