# Phase 3D — Offline Client and Protocol Resilience

Status: `COMPLETED / NEEDS_HUMAN_PHASE_3D_REVIEW`

## Goal

Harden the browser and Protocol v1 boundaries before any real LIFF identity, microphone,
WebSocket, provider or production connection is authorized.

## Mission 1 — Offline browser duplex audio lab

- Convert synthetic Float32 input at browser sample rates to PCM16LE 16 kHz mono, 20 ms frames.
- Define an AudioWorklet capture processor without activating a microphone.
- Prove microphone frames continue while assistant playback is queued.
- Enforce independent input/output backpressure and generation-scoped final playback checks.
- Hard-clear playback on interruption and clear both tracks on idempotent hangup.
- Observe the browser AEC setting as `enabled`, `disabled` or `unreported`; never infer quality.

## Mission 2 — Client state machine

Only explicit transitions among permission, connecting, ready, duplex, interrupting,
reconnecting, failed and ended states are accepted. Ended is terminal. Reconnect requires a new
connection attempt and does not revive old playback.

## Mission 3 — Protocol chaos and replay resistance

- `call.start` must be sequence 1 and carry a valid short-lived call grant.
- Sequence numbers are contiguous; duplicate IDs, reordering and session mismatch fail closed.
- PCM control metadata must describe exactly 640 bytes for one 20 ms frame.
- Input monotonic timestamps must increase.
- Generation commands must address the current server-activated generation.
- Invalid UTF-8, unknown frames, sensitive extras and oversized frames return redacted errors.
- The recent message-ID window is bounded; old replayed frames are still rejected by sequence.

## Mission 4 — Call grant and observability contracts

- HMAC-SHA256 grants bind audience, purpose, session, subject fingerprint, nonce, key ID and time.
- Grant TTL is at most 120 seconds in this contract; verification permits bounded clock skew.
- A nonce is single-use only inside one Python process with a shared validator/guard
  (`VERIFIED_SINGLE_PROCESS_OFFLINE_ONLY`); replay storage is bounded and key rotation accepts only
  configured keys. Multi-worker, multi-container and restart-safe replay rejection are `UNKNOWN`.
- Telemetry accepts allowlisted lifecycle events and machine-safe attributes only.
- Session/generation IDs are hashed; grant, content, transcript, prompt and audio fields are banned.
- Connect, first-audio TTFA and interruption-clear latency use monotonic markers only.

## Mission 5 — Deterministic soak and architecture guard

- 10,000 ordered Protocol v1 frames with bounded replay memory.
- 1,000 reconnects, each requiring a fresh session-bound grant.
- 10,000 telemetry events with a bounded retained tail.
- 1,000 interrupted generations with zero stale playback and zero retained generation records.
- Static boundaries prohibit provider, transport, Pipecat, LiveKit, legacy and network clients.

## Fixed exclusions

- No formal MiniMaxTTSService, Pipecat Pipeline or LiveKit transport.
- No WebSocket server/client, LIFF SDK, `getUserMedia`, provider SDK or external call.
- No real grant signing key, Secret Manager, owner/student identity, transcript, audio or recording.
- No Mem0, external database, LINE OA, deployment, release persona or production.

## Stop

`NEEDS_HUMAN_PHASE_3D_REVIEW`
