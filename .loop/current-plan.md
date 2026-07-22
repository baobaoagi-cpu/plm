# Current Milestone Plan

## Milestone

`LIFF Staging Frontend Bootstrap`

## Goal

Publish the existing backend-free, call-disabled owner-calibration shell at a separate Railway
staging HTTPS endpoint so a human can create the LIFF app without enabling any integration.

## Delivered

- Static Vite entrypoint using the existing owner-calibration shell.
- Separate Railway service `plm-liff-staging-shell` in `staging`.
- Public endpoint `https://plm-liff-staging-shell-staging.up.railway.app/` returned HTTPS 200.
- Call disabled; microphone and all network integrations blocked by code, flags, CSP and
  Permissions-Policy.
- No LINE Secret, access token, LIFF ID or provider credential added.

## Required human action

- In the LINE Login channel, create a LIFF app using the public endpoint.
- Do not send a Channel Secret or Channel Access Token; neither is required for this shell.

## Explicitly not delivered

- LIFF SDK or LINE identity.
- Microphone, WebSocket, MiniMax, LiveKit, database, Mem0 or real-user integration.
- Production deployment, formal voice runtime, or working calls.

## Required stop

`NEEDS_HUMAN_LIFF_APP_CREATION`
