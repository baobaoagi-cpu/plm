# Iteration 021 - LIFF Identity Merge Review Repair

Date: 2026-07-22
Branch: `codex/liff-staging-identity-activation`
Authority: `APPROVED: LIFF Identity Merge Repair`

## Repaired findings

- Split public LIFF configuration from an explicit browser activation flag.
- Replaced the full LIFF SDK import with the approved pluggable surface.
- Enforced staging calibration enablement, kill switch, env-only allowlist and role resolution.
- Bound verified assertions to LINE and the configured Channel audience.
- Detached arbitrary transport exception causes to protect token-bearing request bodies.
- Corrected the microphone UI gate and CSP network policy.
- Pinned CI actions/tool versions, Node range and LIFF dependency; added an explicit npm audit gate.

## Verification

- Ruff: PASS
- mypy strict: PASS, 90 source files
- pytest: PASS, 305 tests
- Frontend lint/typecheck: PASS
- Offline assertions: PASS, 22 protocol + 41 LIFF identity
- Vite synthetic fail-closed build: PASS
- Staging server tests: PASS, 3
- npm audit: PASS, 0 vulnerabilities
- High-confidence secret findings: 0
- Tracy/legacy orchestrator findings: 0

## Boundaries

- No merge.
- No deployment or Railway mutation.
- No production connection.
- No real LINE login or LINE verification transport.
- No microphone, WebSocket, voice provider, database or user data.

Stop: `NEEDS_HUMAN_FINAL_MERGE_REVIEW`
