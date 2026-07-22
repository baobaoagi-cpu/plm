# Phase 3D Offline Client and Protocol Threat Model

## Protected assets

- Verified effective-user binding and one-call session identity.
- Generation ownership and the no-stale-playback invariant.
- Microphone/audio payloads, transcripts, prompts and owner/student data.
- Call-grant signing material and replay nonces.
- Operational events and latency evidence.

## Threats addressed offline

| Threat | Control | Evidence |
|---|---|---|
| Replayed call grant | Bounded process-local nonce store | duplicate token rejected only within one Python process; distributed/restart-safe enforcement UNKNOWN |
| Cross-session or cross-subject grant | Signed session/subject binding | mismatch rejected |
| Wrong audience/purpose/key | Strict signed claims/key ring | rejected |
| Protocol reorder, gap or duplicate | Contiguous sequence + recent message IDs | rejected without state advance |
| Oversized/invalid/sensitive frame | Parse-size limit + redacted error | no payload echo |
| Stale generation command/audio | Active generation equality + final playback check | zero stale playback |
| Unbounded protocol/event memory | Fixed replay/event windows | 10,000-item soak remains bounded |
| Telemetry leaks content or IDs | allowlists, banned keys and SHA-256 fingerprints | sensitive attributes rejected |
| Client lifecycle ambiguity | explicit finite state machine | invalid transitions rejected |
| Hangup/interruption residue | hard queue clear and terminal state | idempotent cleanup |

## Trust boundaries

The server, not the browser, must derive the grant subject from a verified LINE/Partner assertion.
The browser cannot choose `effective_user_id`, tenant, persona, key ID or grant claims. Production
keys must come from a dedicated Secret Manager, support rotation and never enter telemetry.

## Explicitly unproven or deferred

- Real LIFF token verification, WebSocket TLS/origin controls and network denial-of-service.
- Real microphone permissions, AudioContext scheduling, device sample rates and browser AEC quality.
- Pipecat integration, provider cancellation/billing, MiniMax behavior and LiveKit transport.
- Connection-pool identity reset, external staging storage and production key custody.
- XSS/CSP, dependency supply-chain runtime behavior and real-device soak.

These require separate human authorization and staging credentials. No deferred item may be inferred
as verified from this offline phase.
