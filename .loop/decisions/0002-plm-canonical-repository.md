# Decision 0002 — PLM is the canonical Xie Wenxian repository

- Status: accepted
- Date: 2026-07-19
- Authority: explicit project-governance approval

## Decision

`baobaoagi-cpu/plm` is the only canonical repository for the Xie Wenxian Holy Grail persona
candidate assets, owner-calibration sandbox and future LINE OA text/recording/realtime voice system.
The historical `baobaoagi-cpu/holygrail2` branch remains provenance and migration evidence only.

Historical source:

- Repository: `baobaoagi-cpu/holygrail2`
- Branch: `codex/xie-wenxian-soul-container-v0.1`
- Commit: `a1ad3825cf17935622c158795dee019be99bcaaa`

## Migration boundaries

- Pipecat remains the sole conversational orchestrator.
- MiniMax remains `ONE_SESSION_PER_GENERATION`.
- Generation Guard remains the hard output gate.
- Tracy identity, memory, voice, LINE, tenant, cache and evidence assets must not migrate.
- The legacy TypeScript voice pipeline and MiniMax connection pool must not migrate.
- Phase 2 material remains `PROJECT_OWNER_APPROVED_ENGINEERING_INTERPRETATION`.
- The raw V2 prompt is reference-only, untracked and excluded from Git pending governance review.
- No production connection or formal persona release is authorized.

## Stop condition

After migration, verification and GitHub publication, stop at
`NEEDS_HUMAN_PLM_MIGRATION_REVIEW`.
