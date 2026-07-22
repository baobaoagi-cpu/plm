# Holy Grail 3.0 Configuration Contract

Status: `OFFLINE_CONTRACT_WITH_LIFF_IDENTITY_BOUNDARY`

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
- LIFF identity is disabled unless `LIFF_IDENTITY_ENABLED=true`, `APP_ENV=staging`, sandbox mode is
  on, and both public Channel ID and LIFF ID are configured.
- The LIFF ID, LIFF URL, LINE Login Channel ID and official issuer are public configuration. They
  are not credentials.

## Value classes

| Class | Examples | Storage |
|---|---|---|
| Secret | API keys, channel secret, access token, Voice ID, signing keys, database URLs | Approved Secret Manager or process environment only |
| Sensitive config | LINE allowlist | Approved Secret Manager or process environment only |
| Server config | enable flags, model names, provider names, transport URL | Server environment |
| Public config | LIFF ID, LIFF URL, LINE Login Channel ID, issuer, public WebSocket URL | May be injected into the browser build or server environment |

The machine-readable classification is `ENVIRONMENT_CONTRACT` in
`src/duplex_voice/config.py`. Diagnostic snapshots contain only safe flags and format settings;
they never include configured values from secret slots.

## Activation boundary

Populating a slot is not permission to use it. A later human milestone must switch from
`offline_hardening` to `staging_integration` and independently authorize each integration flag.
Production remains outside this contract.

## LIFF staging identity slots

| Variable | Class | Current repository value | Apply only after review |
|---|---|---|---|
| `VITE_LIFF_ID` | `PUBLIC_CONFIG` | empty | Public LIFF ID for the browser build |
| `XIEWENXIAN_CALIBRATION_LIFF_ID` | `PUBLIC_CONFIG` | empty | Same public LIFF ID for server binding |
| `XIEWENXIAN_CALIBRATION_LINE_CHANNEL_ID` | `PUBLIC_CONFIG` | empty | Expected audience for LINE verification |
| `XIEWENXIAN_CALIBRATION_LINE_ISSUER` | `PUBLIC_CONFIG` | `https://access.line.me` | Official expected issuer |
| `LIFF_IDENTITY_ENABLED` | `SERVER_CONFIG` | `false` | Explicit identity-only activation flag |

The Channel Secret and Channel Access Token are not required by the ID-token verification contract
and remain empty. A human must provide the public Channel ID before any future staging activation.
This Mission does not modify Railway variables.
