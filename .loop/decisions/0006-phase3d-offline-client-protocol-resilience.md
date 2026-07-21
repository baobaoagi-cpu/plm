# Decision 0006 — Phase 3D hardens client/protocol boundaries without connecting them

- Status: accepted
- Date: 2026-07-21
- Authority: explicit human approval for `Phase 3D — Offline Client and Protocol Resilience`

## Decision

Implement the browser audio, lifecycle, grant, replay, telemetry and soak boundaries as pure local
logic. Compile the AudioWorklet but do not connect `getUserMedia`, WebSocket, LIFF, provider or
production infrastructure.

Call grants are mechanics only: synthetic test keys prove audience/purpose/session/subject/nonce
binding and rotation. A later authorized server boundary must source signing keys from a dedicated
Secret Manager and derive the subject from verified identity.

## Architecture preservation

- Pipecat remains the sole future orchestrator.
- Generation Guard remains the final output admission gate.
- MiniMax remains one WebSocket session per generation when formally implemented.
- No legacy voice pipeline, connection pool or LiveKit Agent runtime is introduced.

## Stop

`NEEDS_HUMAN_PHASE_3D_REVIEW`
