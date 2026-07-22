# Current Milestone Plan

## Milestone

`LIFF Identity Merge Review Repair`

## Goal

Repair the expert-review blockers in Draft PR #10 while preserving its offline-only boundary and
without merging, deploying or connecting production.

## Delivered

- Human screenshot settings mapped to `HUMAN_SCREENSHOT_VERIFIED`; the screenshot is not committed.
- Official LIFF SDK adapter uses init, login-state observation and opaque ID-token retrieval only.
- Missing public build config prevents SDK loading and all identity failures keep media/call off.
- Server verifier contract uses LINE's official verify endpoint and validates issuer, audience,
  expiry and subject before the existing Phase 3B effective-user mapping.
- Raw token/subject are excluded from repr, events, responses and persistence.
- Public LIFF ID possession no longer activates the SDK; an explicit browser flag is required.
- The pluggable SDK exposes only core initialization, login-state observation and opaque ID-token
  retrieval.
- Existing allowlist, kill switch and role policy are enforced after official provider validation.
- Provider and Channel audience confusion is rejected before Phase 3B mapping.
- Arbitrary upstream exception causes are detached before safe errors cross the boundary.
- CSP permits the LINE API required by LIFF initialization while retaining microphone/media denial.
- Railway, production, DB, Mem0, microphone, WebSocket and voice services remain unchanged/off.

## Required human action

- Review the repaired Draft PR, its CI evidence and stacked merge order.
- A separate authorization is still required for deployment and consented real-login staging.

## Explicitly not delivered

- Deployment, real LIFF initialization/login or LINE network verification.
- Profile, email, friendship, chat-message, QR or share-target access.
- Microphone, WebSocket, MiniMax, LiveKit, database, Mem0 or real-user integration.
- Production deployment, formal voice runtime, or working calls.
- Railway or runtime injection of the public LIFF ID.

## Required stop

`NEEDS_HUMAN_FINAL_MERGE_REVIEW`
