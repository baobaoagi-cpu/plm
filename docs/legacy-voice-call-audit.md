# Legacy Voice Call Feature Extraction Audit

## Status and scope

Status: `COMPLETE`

This is a read-only audit of the Legacy Reference Repository. No reference file was modified, no
legacy code was copied into PLM, no provider API was called, and no integration or Task 004 work
was started.

Reference:

- Path: `C:\Users\waiti\PLM\references\Mindomind-voice-call-package`
- Branch: `voice-call-package`
- Commit: `2ae148d46b5d018ae5999ee68f3db6da5cc5566f`
- Worktree: clean
- Package: `voice-call-feature/`, 43 files (15 backend, 27 frontend, 1 root README)

Evidence labels used below:

- `VERIFIED`: directly observed in code or Git metadata.
- `INFERRED`: engineering conclusion derived from observed code plus the PLM specification.
- `UNKNOWN`: cannot be established without runtime testing, missing shared dependencies, or future
  integration authority.

The complete per-file inventory is in `.loop/evidence/legacy-package-inventory.json`.

## Reuse classification

| Module | Classification | Reason and code evidence | Status |
|---|---|---|---|
| LIFF initialization | `REUSE_WITH_ADAPTER` | `frontend/src/lib/liff.ts:initLiff` initializes LIFF and retrieves a profile, but its returned `userId` is later trusted by the WS server without token verification. | VERIFIED |
| CallScreen | `REUSE_WITH_ADAPTER` | `frontend/src/components/CallScreen.tsx:CallScreen` is useful UI, but imports legacy health, monologue, rain and state semantics. | VERIFIED |
| useWebSocket | `REWRITE` | `frontend/src/hooks/useWebSocket.ts:78-247` has an unversioned union, no auth token, generation, sequence, ACK or reconnect policy. | VERIFIED |
| useAudio | `REWRITE` | `frontend/src/hooks/useAudio.ts:141-225,291-552` mixes capture, VAD, mic gating, MP3 decode, PCM buffering and playback in one hook. | VERIFIED |
| BreathingOrb | `REUSE_AS_IS` | Pure React/canvas visualization driven by state and volume getters; no provider binding. | VERIFIED |
| Waveform | `REUSE_AS_IS` | Pure React/canvas animation with no session or provider state. | VERIFIED |
| MicPermission | `REUSE_AS_IS` | Presentational allow/deny component with no provider dependency. It is currently not wired by `App.tsx`. | VERIFIED |
| DialTone | `REUSE_AS_IS` | Local Web Audio dial tone with timer cleanup; no backend dependency. | VERIFIED |
| voice-call-trigger | `REUSE_WITH_ADAPTER` | Keyword and Flex-card concepts are reusable, but `voice-call-trigger.ts:63-208` depends on legacy config, LINE Push API and embeds identity/session parameters in a URL. | VERIFIED |
| voice-session | `REWRITE` | `voice-session.ts:38-118` binds LINE IDs, DB, persona and context; the optional incoming session ID is ignored and identity is accepted from the caller. | VERIFIED |
| voice-pipeline | `DEPRECATE` | `voice-pipeline.ts:1-18,63-159` is a second orchestrator and state owner, conflicting with Pipecat as the sole orchestration core. Test scenarios may be extracted, not the class. | VERIFIED |
| streaming-asr | `EXTRACT_LOGIC_ONLY` | `streaming-asr.ts:95-319` contains useful endpointing/reconnect cases but is a TypeScript Deepgram client, while the target runtime is Python/Pipecat. | VERIFIED |
| minimax-realtime | `DEPRECATE` | `minimax-realtime.ts:1-15,79-109,278-357` assumes repeated tasks on a pooled WS; Task 002 rejected the second `task_start` with 2206. | VERIFIED |
| minimax-tts | `DEPRECATE` | HTTP/SSE engine conflicts with the formal MiniMax WebSocket output engine. Header claims PCM while request specifies MP3 (`minimax-tts.ts:1-11,322-327`). Circuit-breaker cases remain useful as tests. | VERIFIED |
| mouth | `EXTRACT_LOGIC_ONLY` | Large mixed module combining text cleanup, emotion, multiple TTS vendors, DB/config, R2 and logging. Only pure normalization rules are candidates. | VERIFIED |
| ear | `EXTRACT_LOGIC_ONLY` | `ear.ts` mixes Deepgram batch STT, LINE content download, DB/config and correction rules; only test cases/correction logic are portable. | VERIFIED |
| voice-judge | `EXTRACT_LOGIC_ONLY` | `voice-judge.ts:48-133` has useful acknowledgement/advisory cases, but invokes a second LLM decision path and cannot own the new floor state. | VERIFIED |
| echo-filter | `EXTRACT_LOGIC_ONLY` | Text similarity heuristics in `echo-filter.ts:19-62` can be auxiliary evidence, but cannot replace browser AEC or far-end reference handling. | VERIFIED |
| bg-filter | `EXTRACT_LOGIC_ONLY` | Pure threshold/pattern ideas are portable as tests; fixed Mandarin heuristics require calibration in the new runtime. | VERIFIED |
| tts-player | `EXTRACT_LOGIC_ONLY` | `tts-player.ts:31-230` has queue, abort, filler and circuit-breaker scenarios, but imports legacy TTS engines and owns orchestration state. | VERIFIED |
| utils | `EXTRACT_LOGIC_ONLY` | `utils.ts` contains pure text rules and PCM-to-WAV logic suitable for porting with Python tests. | VERIFIED |

Classification totals for these required modules:

- `REUSE_AS_IS`: 4
- `REUSE_WITH_ADAPTER`: 3
- `EXTRACT_LOGIC_ONLY`: 7
- `REWRITE`: 3
- `DEPRECATE`: 3
- `UNKNOWN`: 0

## Major conflicts

1. **MiniMax session reuse:** the global pool and same-socket repeated tasks in
   `backend/modules/minimax-realtime.ts:53-109,193-200,278-357` conflict with Task 002's verified
   `ONE_SESSION_PER_GENERATION`. Classification: `DEPRECATE`. `VERIFIED`.
2. **Mic gating during AI playback:** `frontend/src/hooks/useAudio.ts:209-225` runs RMS VAD but
   returns before emitting PCM whenever playback buffers or the 400 ms tail gate are active. This
   conflicts with continuous duplex upload. `VERIFIED`.
3. **Dual orchestrators:** `backend/modules/voice-pipeline.ts:1-18,78-159` owns ASR, interruption,
   brain, TTS queue and session phases. It cannot coexist as an orchestrator beside Pipecat.
   `VERIFIED`.
4. **Service boundary:** the legacy Fastify/TypeScript route constructs the pipeline directly at
   `backend/routes/voice-call.ts:319-323`; the target boundary is LIFF WebSocket to Python Voice
   Runtime. An explicit versioned adapter is required. `INFERRED`.
5. **MP3 versus PCM:** browser playback is MP3-to-PCM at 24 kHz
   (`useAudio.ts:291-467`). HTTP TTS comments claim PCM but request MP3
   (`minimax-tts.ts:1-11,322-327`). Task 002 verified MP3. Future PCM remains `UNKNOWN` until a
   separately authorized probe.
6. **Echo Filter versus AEC:** browser `getUserMedia` requests `echoCancellation: true`
   (`useAudio.ts:151-163`), while backend echo filtering is transcript similarity
   (`echo-filter.ts:39-62`). The latter is only an auxiliary heuristic. `VERIFIED`.
7. **Boolean state versus Floor State Machine:** the pipeline declares a phase but explicitly keeps
   `isSpeaking`, `isGreeting`, `isProcessing`, pending and interruption flags
   (`voice-pipeline.ts:63-75,151-159`). Divergent combinations are possible. `VERIFIED`.
8. **Session identity:** the frontend sends `userId` in `call:start`
   (`useWebSocket.ts:101-110`); the backend trusts it for DB lookup
   (`voice-call.ts:293-350`, `voice-session.ts:38-59`) without a LIFF ID-token proof. A verified
   server-side LINE identity exchange is required. `VERIFIED`.

Additional risks and priorities are in `.loop/evidence/legacy-package-risk-register.json`.

Tooling note: repository-wide `ruff check .` traverses the complete nested legacy clone and reports
641 pre-existing findings outside the 43-file feature package. No auto-fix was run. PLM validation
was scoped to `src scripts tests` and passed. A future explicitly approved tooling change should
exclude `references/` rather than modifying legacy files. `VERIFIED`.

## Valuable legacy acceptance scenarios

- Duplicate call connection closes the old session without destroying the new one
  (`voice-call.ts:302-332,418-425`).
- `call:end` and socket close finalize idempotently (`voice-call.ts:373-399,408-438`).
- AI-time mic audio continues uploading while local VAD distinguishes echo, acknowledgement and
  true interruption. This is a new regression test derived from the observed gating defect.
- Late TTS chunks after interrupt never reach playback; generation mismatch discards them.
- MP3 chunks below/above the 2,048-byte decode threshold and incomplete final frames flush safely
  (`useAudio.ts:444-482`).
- `audio:clear` discards buffers, whereas `audio:done` flushes and drains
  (`App.tsx:62-72`).
- Fade-out is bounded and followed by hard clear (`useAudio.ts:522-552`).
- TTS zero-chunk, retry, circuit-open and filler cooldown cases
  (`minimax-tts.ts:204-280`, `tts-player.ts:152-227`).
- ASR reconnect, pending-audio handling, keepalive and close cleanup
  (`streaming-asr.ts:79-99,141-158,227-319`).
- Echo-like interim transcript must not interrupt; semantically distinct sustained speech must.
- All media tracks, AudioContexts, processors, timers and buffers clear on hangup/unmount
  (`useAudio.ts:238-257,484-520,652-669`).
- Untrusted/mismatched `userId` is rejected before session construction.
- Playback buffers and pre-connect ASR buffers have explicit memory caps.

## Security audit

- `frontend/.env.example`: tracked; variable names `VITE_LIFF_ID`, `VITE_WS_URL`; no high-confidence
  secret pattern. Status: `SAFE`.
- `frontend/.env.production`: tracked; variable names `VITE_LIFF_ID`, `VITE_WS_URL`; no
  high-confidence key, JWT, bearer token or private-key pattern. Status: `SAFE`, but values must not
  be copied into PLM and should receive deployment-owner review before reuse.
- No env value was written to this report or evidence.
- Runtime code references additional external configuration not included in the package:
  `DEBUG_TTS`, `GODVIEW_SELF_LINE_ID`, `LINE_IDENTITY_MAP`, `RAILWAY_PUBLIC_DOMAIN`,
  `VOICE_JUDGE_ENABLED`, plus shared `config` secrets.
- Sensitive logging risk: MiniMax modules log text excerpts, provider messages, trace IDs and error
  bodies (`minimax-realtime.ts:161,175,205-208,337`; `minimax-tts.ts:202,256,342-346,391-411`).
  These patterns must not be ported.
- Identity risk: WebSocket `userId` is caller-controlled and not proven by a LIFF token.

## Recommended extraction plan

### Stage 1 — LIFF shell and reusable UX

- Allowed future files: new copies/adapters of `lib/liff.ts`, `CallScreen`, `BreathingOrb`,
  `Waveform`, `MicPermission`, `DialTone`, avatar/style assets and a minimal App shell.
- Forbidden: legacy `useAudio`, `useWebSocket`, all backend modules and `.env.production`.
- Dependencies: approved LINE LIFF app configuration, frontend package boundary, UX asset review.
- Acceptance: LIFF init/login/profile errors tested; mic permission gesture tested; UI renders without
  backend, provider or real secrets.
- Rollback: remove the isolated frontend feature flag/package; no runtime migration.
- Human approval: required before extraction.

### Stage 2 — Versioned WebSocket protocol and Python boundary

- Allowed future files: new frontend protocol client and Python protocol/transport adapter in
  explicitly approved paths.
- Forbidden: legacy TypeScript pipeline, MiniMax engines, same-session connection pool and implicit
  binary frames without negotiated format.
- Dependencies: authenticated LINE identity design, protocol version, session/generation/message
  identifiers, schema validation, error codes and heartbeat policy.
- Acceptance: contract tests for every message, invalid payloads, auth mismatch, reconnect,
  ordering, duplicate messages and binary framing.
- Rollback: disable the new protocol version and retain the isolated UI shell.
- Human approval: required.

### Stage 3 — Continuous audio, playback and hard interruption

- Allowed future files: a rewritten AudioWorklet-based capture/playback layer, generation-aware
  buffers and protocol handlers after the relevant milestones are authorized.
- Forbidden: ScriptProcessor mic gating, legacy connection pool, legacy TTSPlayer orchestration and
  treating socket close as provider cancellation proof.
- Dependencies: approved Generation Guard milestone, formal MiniMax service milestone, continuous
  upload/AEC design and memory budgets.
- Acceptance: mic uploads throughout AI playback; stale generation chunks are discarded; local
  playback clears immediately; MP3 decode/drain and cleanup tests pass; measurable latency budget.
- Rollback: feature flag to the Stage 2 shell with audio disabled, closing all media resources.
- Human approval: required.

## Final gate

Audit complete. The next permitted action is human review of the extraction plan. The project must
remain at `NEEDS_HUMAN_EXTRACTION_PLAN_APPROVAL`; no integration or Task 004 is authorized.
