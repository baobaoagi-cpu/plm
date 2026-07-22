# Current Milestone Plan

## Milestone

`LIFF Staging Identity Activation — implementation and offline verification only`

## Goal

Implement an openid-only LIFF client seam and a fail-closed server verification boundary that reuses
the Phase 3B tenant-bound identity mapper, using offline fixtures only.

## Delivered

- Human screenshot settings mapped to `HUMAN_SCREENSHOT_VERIFIED`; the screenshot is not committed.
- Official LIFF SDK adapter uses init, login-state observation and opaque ID-token retrieval only.
- Missing public build config prevents SDK loading and all identity failures keep media/call off.
- Server verifier contract uses LINE's official verify endpoint and validates issuer, audience,
  expiry and subject before the existing Phase 3B effective-user mapping.
- Raw token/subject are excluded from repr, events, responses and persistence.
- Railway, production, DB, Mem0, microphone, WebSocket and voice services remain unchanged/off.

## Required human action

- Review the offline identity implementation and decide whether to authorize a separate deployment
  and consented real-login staging gate.
- Supply the public LINE Login Channel ID only under that later gate.

## Explicitly not delivered

- Deployment, real LIFF initialization/login or LINE network verification.
- Profile, email, friendship, chat-message, QR or share-target access.
- Microphone, WebSocket, MiniMax, LiveKit, database, Mem0 or real-user integration.
- Production deployment, formal voice runtime, or working calls.
- Railway or runtime injection of the public LIFF ID.

## Required stop

`NEEDS_HUMAN_LIFF_IDENTITY_ACTIVATION_REVIEW`
