# Legacy Voice Call WebSocket Protocol

## Scope

Observed implementation, not a proposed new protocol. There is no version discriminator, schema
validator, authenticated identity proof, generation ID, message ID, sequence, ACK or structured
error code. All future-reusable concepts therefore require versioning.

Primary evidence:

- Client: `voice-call-feature/frontend/src/hooks/useWebSocket.ts:18-29,78-247`
- Server: `voice-call-feature/backend/routes/voice-call.ts:34-52,171-445`
- Server event producers: `voice-call-feature/backend/modules/voice-pipeline.ts`

## Client to server

| Event | Transport | Payload | Required / optional | Legacy-only | Future reusable | Needs versioning | Evidence |
|---|---|---|---|---|---|---|---|
| `call:start` | JSON text | `{type,userId,sessionId?}` | `type`, `userId`; `sessionId` optional | Current identity semantics yes | Concept yes, payload no | Yes | `useWebSocket.ts:101-110`; `voice-call.ts:293-350` |
| microphone audio | binary | raw PCM signed 16-bit little-endian, 16 kHz, mono | entire frame implicit | Framing yes | Audio upload yes | Yes | `useAudio.ts:151-224`; `voice-call.ts:219-241` |
| `audio:interrupt` | JSON text | `{type}` | `type` | Current no-generation semantics yes | Concept yes | Yes | `useWebSocket.ts:211-216`; `voice-call.ts:360-370` |
| `call:end` | JSON text | `{type}` | `type` | Current finalize semantics yes | Concept yes | Yes | `useWebSocket.ts:218-227`; `voice-call.ts:373-400` |

The comment mentions `audio:chunk`, but the implementation sends audio as an unlabelled binary
frame. `audio:chunk` is therefore documentation-only, not an implemented JSON event. `VERIFIED`.

## Server to client

| Event | Transport | Payload | Required / optional | Legacy-only | Future reusable | Needs versioning | Evidence |
|---|---|---|---|---|---|---|---|
| `call:ready` | JSON text | `{type,greeting,userName}` | `type`; strings effectively optional client-side | Identity/greeting shape yes | Concept yes | Yes | `voice-call.ts:345-350`; `useWebSocket.ts:123-127` |
| TTS audio | binary | MP3 bytes | implicit codec/rate/channel | Implicit format yes | Binary delivery yes | Yes | `voice-pipeline.ts:626,1133-1136`; `useWebSocket.ts:112-117` |
| `audio:stream` | JSON text fallback | `{type,data}` with base64 audio | `type`; `data` optional | Yes | No preferred path | Yes | `useWebSocket.ts:129-135` |
| `audio:done` | JSON text | `{type}` | `type` | Current drain semantics yes | Concept yes | Yes | `voice-pipeline.ts:668-669,849-855`; `App.tsx:62-64` |
| `audio:clear` | JSON text | `{type}` | `type` | No generation target | Concept yes | Yes | `voice-pipeline.ts:718-721`; `App.tsx:65-69` |
| `audio:fadeout` | JSON text | `{type}` | `type` | Fixed 300 ms legacy behavior | UX concept yes | Yes | `voice-pipeline.ts:899-923`; `useAudio.ts:522-552` |
| `status` | JSON text | `{type,state}` | `type`; state optional client-side | Boolean/phase projection yes | Concept yes | Yes | `useWebSocket.ts:12-29,151-156`; pipeline send sites |
| `filler` | JSON text | `{type,index}` | `type`; index defaults to 0 | Asset-index coupling yes | UX pattern maybe | Yes | `tts-player.ts:169-179,217-226`; `useWebSocket.ts:158-160` |
| `fx:tool` | JSON text | `{type,tool,phase}` | all for effect | Legacy brain/tool names yes | Optional UX concept | Yes | `voice-pipeline.ts:703`; `useWebSocket.ts:162-167` |
| `location:request` | JSON text | `{type,reason?}` | `type`; reason optional | Product-specific | Possibly | Yes | `useWebSocket.ts:169-171`; route location bridge imports |
| `error` | JSON text | `{type,message}` | `type`; message optional | Unstructured string yes | Error concept yes | Yes | `voice-call.ts:298,402-405`; `useWebSocket.ts:173-176` |
| `call:ended` | JSON text | `{type}` | `type` | Current lifecycle semantics yes | Concept yes | Yes | `voice-call.ts:391-399`; `useWebSocket.ts:178-181` |

Known `status.state` values are `listening`, `hearing`, `thinking`, `speaking`, `interrupting` on the
client. The backend emits the first four; `interrupting` is set locally by `App.tsx:30-37`.

## Session and transport lifecycle

1. Browser opens WS and sends `call:start` on `open`.
2. Server closes any old connection with the same caller-supplied `userId`.
3. Server creates DB-backed session and legacy pipeline, sends `call:ready`, then starts greeting.
4. Browser sends raw PCM frames. Server always calls `pipeline.onAudioChunk` for received frames,
   but browser-side `useAudio` suppresses frames during AI playback.
5. Either peer initiates interruption; backend sends status/audio control events.
6. `call:end` destroys pipeline, ends session, sends `call:ended` and closes WS.
7. Socket close repeats idempotent cleanup.
8. WS ping/pong is used every 15 seconds; 45 seconds without pong closes the socket
   (`voice-call.ts:189-205`). This is transport health, not an application message.

## Missing health and debug protocol

- No WebSocket `health` or `debug` event is implemented. `HealthIndicator.tsx` polls HTTP instead.
- Parse failures return only `error.message`; there is no code, correlation ID or retryability.
- Unknown client JSON types are silently ignored by the switch.
- Client JSON parsing catches and logs without protocol error recovery.

## Required vNext additions

- `protocol_version`
- authenticated server-derived LINE identity; never trust payload `userId`
- `session_id`, `generation_id`, `message_id`, monotonic `sequence`
- explicit binary envelope or negotiated input/output format
- structured error `{code,message,retryable,trace_id}` with redaction
- interruption request/ack and playback-clear semantics scoped to generation
- reconnect/resume policy and idempotency keys
- schema validation and unknown-version rejection
- size/rate/memory limits for JSON and binary frames

All vNext design choices remain `INFERRED` recommendations pending human extraction-plan approval.
