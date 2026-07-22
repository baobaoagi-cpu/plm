# Iteration 011 — Xie Wenxian PLM migration repair

## Goal

Repair the confirmed repository-ownership error by inventorying the historical HolyGrail2 assets,
migrating only governed persona material, reimplementing Phase 3A isolation in the PLM Python
package, and introducing a disabled LIFF calibration shell without production integrations.

## Source and target

- Canonical target: `baobaoagi-cpu/plm`
- Repair branch: `codex/xie-wenxian-plm-migration`
- Historical source: `baobaoagi-cpu/holygrail2`
- Historical branch: `codex/xie-wenxian-soul-container-v0.1`
- Historical commit: `a1ad3825cf17935622c158795dee019be99bcaaa`

## Implemented scope

- Classified 31 source assets with source hashes, target mappings, isolation requirements and
  migration decisions.
- Migrated 46 Phase 2 candidates and 15 unanswered owner-confirmation items without promoting any
  candidate or adding any owner quote.
- Reimplemented fail-closed Phase 3A identity isolation under `duplex_voice.calibration`.
- Added independent tenant/persona/memory/storage/cache/session/LINE/voice configuration slots.
- Added a call-disabled, backend-free React LIFF calibration shell.
- Kept the raw V2 source reference-only and ignored by Git.
- Did not migrate Tracy assets, the legacy voice pipeline, MiniMax connection pooling or a second
  orchestrator.

## Validation

The final evidence record is `.loop/evidence/xiewenxian-plm-migration-i11.json`. Local gates cover
Ruff, mypy strict, the complete pytest suite, strict TypeScript, npm audit, secret scanning,
forbidden-import scanning, Tracy-contamination scanning, namespace isolation and Git diff checks.

Decision: `COMPLETE`

Draft PR: `https://github.com/baobaoagi-cpu/plm/pull/1`

GitHub Actions: `PASS`

Next allowed action: human PLM migration review. Production and Task 005 remain unauthorized.
