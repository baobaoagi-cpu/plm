# Current Milestone Plan

## Milestone

`Phase 3D — Offline Client and Protocol Resilience`

## Goal

Harden browser audio framing, client lifecycle, call grants, Protocol v1 ordering/replay and safe
observability before any real identity, transport, microphone or provider integration.

## Delivered locally

- PCM16LE 16 kHz mono 20 ms browser framer and unconnected AudioWorklet capture contract.
- Independent offline microphone/playback queues with backpressure, hard clear and final generation
  admission check.
- Explicit client permission/connect/duplex/interrupt/reconnect/hangup state machine.
- Short-lived HMAC call grant with audience/purpose/session/subject/nonce/time binding and rotation.
- Protocol ingress gate for order, replay, session, audio timestamp and generation validation.
- Bounded redacted lifecycle events and monotonic latency metrics.
- Threat model, architecture-boundary tests and deterministic high-volume soak.

## Verified

- 10,000 ordered protocol frames; replay ID tail bounded at 64.
- 1,000 reconnects; every connection used a fresh session-bound grant.
- 10,000 telemetry events; retained tail bounded at 128.
- 1,000 interrupted generations; zero stale playback and zero terminal records retained.
- Ruff, mypy strict, 261 pytest tests, TypeScript strict and 19 browser assertions passed.

## Pending human action

- Human Phase 3D review.

## Explicitly not delivered

- Real `getUserMedia`, LIFF identity SDK, WebSocket client/server or device AEC validation.
- Formal MiniMaxTTSService, Pipecat Pipeline, LiveKit transport or provider adapter.
- Real signing key, external database, LINE OA, Mem0, R2, owner/student data or recordings.
- Phase 3E, Task 005, release persona or production deployment.

## Required stop

`NEEDS_HUMAN_PHASE_3D_REVIEW`
