# Decision 0003 — Phase 3B uses a provider-neutral staging database contract

- Status: accepted
- Date: 2026-07-20
- Authority: explicit Phase 3B human approval plus existing PLM architecture decisions

## Decision

Phase 3B defines PostgreSQL 15+ SQL under the dedicated `xiewenxian_staging` schema but does not
connect to or mutate an external database. The current environment has no confirmed staging DB
identity, retention policy, application roles or rollback window.

The migration therefore includes:

- fixed staging tenant/environment checks;
- composite tenant/principal/principal-kind foreign keys;
- forced RLS on every table;
- indexes for foreign keys and RLS lookup paths;
- conditional grants only when persona-specific staging roles already exist;
- no Supabase-specific `anon` or `authenticated` role assumptions;
- staging-only rollback guard.

## Identity and content boundary

Only a verified external assertion may map to an effective user ID. Raw external IDs are reduced to
a stable SHA-256 fingerprint. The proof store rejects any content not explicitly labelled
`synthetic:` and stores digests only.

## Conflict resolution

The historical infrastructure guide recommends hard-coding Voice IDs. PLM governance requires all
Voice IDs and secrets to come from environment variables or an approved Secret Manager. PLM
governance wins; Phase 3B does not add or read a Voice ID.

## Stop

External database execution requires a later human decision. Phase 3B stops at
`NEEDS_HUMAN_PHASE_3B_REVIEW`.
