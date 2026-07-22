# Iteration 018 — LIFF Staging Frontend Bootstrap

- Built the existing owner-calibration React shell as a static Vite application.
- Kept call, microphone, WebSocket, LINE identity, MiniMax, LiveKit, and database paths disabled.
- Added a dependency-free staging-only static server with health and browser security headers.
- Created a separate Railway staging frontend service and verified public HTTPS 200 responses.
- The first builds exposed a duplicate Railpack install command; the deterministic build setting was
  corrected without changing runtime scope or acceptance criteria.
- No production service, secret, token, real user, audio, or provider was used.
- Validation: Ruff pass; mypy strict 87 files; pytest 278; TypeScript pass; offline assertions 22;
  staging tests 3; Vite build pass; npm audit 0 vulnerabilities.
- Stop: `NEEDS_HUMAN_LIFF_APP_CREATION`.
