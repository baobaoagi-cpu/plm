# Holy Grail 3.0 Configuration Contract

Status: `OFFLINE_CONTRACT_ONLY`

This contract is for the Xie Wenxian owner-calibration sandbox. It creates no provider, LINE,
database, LiveKit or production connection. Empty slots in `.env.example` are intentional.

## Fail-closed invariants

- `APP_ENV` may only be `development`, `test` or `staging` in Phase 3C.
- Offline hardening rejects every external integration enable flag.
- Sandbox mode and the kill switch are on by default.
- MiniMax output remains verified MP3, 24 kHz, mono.
- MiniMax uses exactly one WebSocket session per generation.
- Generation Guard cannot be disabled and stale generations are always discarded.
- Audio dumps are forbidden in this phase.
- Secrets and sensitive allowlists are server-only; no secret may use a `VITE_` prefix.

## Value classes

| Class | Examples | Storage |
|---|---|---|
| Secret | API keys, channel secret, access token, Voice ID, signing keys, database URLs | Approved Secret Manager or process environment only |
| Sensitive config | LINE allowlist | Approved Secret Manager or process environment only |
| Server config | model names, channel ID, provider names, transport URL | Server environment |
| Public config | LIFF ID, public WebSocket URL | May be injected into the browser build |

The machine-readable classification is `ENVIRONMENT_CONTRACT` in
`src/duplex_voice/config.py`. Diagnostic snapshots contain only safe flags and format settings;
they never include configured values from secret slots.

## Activation boundary

Populating a slot is not permission to use it. A later human milestone must switch from
`offline_hardening` to `staging_integration` and independently authorize each integration flag.
Production remains outside this contract.
