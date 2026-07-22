# Current Milestone Plan

## Milestone

`LIFF App Registration Verification and Public Configuration Contract`

## Goal

Verify the human-created public LIFF registration without authenticating a real user, then record
the LIFF ID, LIFF URL and endpoint as public configuration without activating any integration.

## Delivered

- LIFF public URL returned HTTP 200 and exposed the expected app name and LIFF ID.
- Public landing HTML uses client-side JavaScript plus a fallback link to the expected staging
  endpoint; there is no HTTP 3xx redirect.
- Staging endpoint and health returned HTTP 200 with integrations false.
- LIFF ID, LIFF URL and endpoint are classified as `PUBLIC_CONFIG`.
- No credential was added and the LIFF ID was not injected into Railway or runtime configuration.

## Required human action

- Review this public-registration evidence and decide whether to authorize a separate LIFF identity
  activation milestone.
- Treat openid as `HUMAN_CONFIGURED_NOT_SCREENSHOT_VERIFIED`; profile and chat scopes remain
  `UNKNOWN_NOT_SCREENSHOT_VERIFIED`.

## Explicitly not delivered

- LIFF SDK initialization, LINE identity or profile access.
- Microphone, WebSocket, MiniMax, LiveKit, database, Mem0 or real-user integration.
- Production deployment, formal voice runtime, or working calls.
- Railway or runtime injection of the public LIFF ID.

## Required stop

`NEEDS_HUMAN_LIFF_IDENTITY_ACTIVATION_REVIEW`
