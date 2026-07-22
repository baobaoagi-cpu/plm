# Iteration 020 — LIFF Staging Identity Activation

Status: `COMPLETED_OFFLINE_ONLY / NEEDS_HUMAN_LIFF_IDENTITY_ACTIVATION_REVIEW`

## Goal

Implement a fail-closed openid-only LIFF client seam and server-side LINE ID-token verification
boundary while preserving the existing Phase 3B tenant mapping.

## Scope retained

- Official LIFF SDK is dynamically loaded only with valid public build configuration.
- LINE verification network access is represented by an injected transport and deterministic fake.
- No real user, provider, database, memory, microphone, WebSocket or voice runtime is used.
- Call controls remain disabled and Railway is unchanged.

## Evidence boundary

Human screenshot verification covers the LIFF Console settings but the screenshot itself is not
committed. Offline fixtures prove software behavior only and do not prove a real LINE login.

## Validation

- `uv run ruff check .`: pass.
- `uv run mypy`: pass, 90 files.
- `uv run pytest tests/unit`: pass, 297 tests.
- `npm run lint`: pass, two identity entry files scanned.
- `npm run typecheck`: pass.
- `npm run test:offline`: pass, 22 existing plus 24 identity assertions.
- `npm run test:staging`: pass, 3 tests.
- `npm run build`: pass.
- `npm ci --ignore-scripts`: pass; `npm audit`: 0 vulnerabilities.
- Six JSON files parsed successfully.
- Secret scan: 0 high-confidence findings in 27 Mission files.
- Forbidden runtime and client API scans: 0 matches.

External LINE calls, real logins, DB/Mem0 operations, deployments and production changes: `0`.

Required stop: `NEEDS_HUMAN_LIFF_IDENTITY_ACTIVATION_REVIEW`.
