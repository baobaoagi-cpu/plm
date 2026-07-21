# Phase 3C — Offline Duplex Architecture Hardening

Status: `LOCAL_ACCEPTANCE_COMPLETE / GITHUB_ACTIONS_PENDING`

## Authority and scope

Human approval authorizes four offline missions only:

1. complete the environment contract and fail-closed configuration;
2. define protocol v1 and a stale-safe session registry;
3. prove independent listen/speak queues and Generation Guard races with synthetic audio;
4. define provider-neutral adapters, reusable fakes and bounded fault injection.

The local PostgreSQL execution is a separate gate and is not part of this milestone.

## Hard boundaries

- Pipecat remains the only future orchestrator; this milestone creates no Pipeline.
- MiniMax remains one WebSocket session per generation; no pool is introduced.
- Generation Guard is the final admission gate before playback.
- All data is synthetic. No provider, LINE, database, Mem0, R2, LiveKit or production endpoint is
  contacted.
- No release persona, owner evidence upgrade, real identity, recording or public voice is created.
- Tracy assets, credentials, namespaces and runtime remain excluded.

## Acceptance

- `.env.example` and the machine-readable contract have identical variable names.
- Production, disabled Generation Guard, connection pooling, stale playback and external flags all
  fail closed in offline mode.
- Protocol v1 rejects unknown versions/types, oversized frames, extra identity fields and invalid
  audio formats without echoing sensitive input.
- A stale transport lease cannot delete its replacement.
- Microphone frames continue to enter an independently bounded input queue during assistant output.
- Cancelled/superseded generation audio cannot pass the final pre-playback check.
- A 40-way enqueue/interrupt race and 100 sequential interruptions produce zero stale playback.
- STT, LLM, TTS, identity and transport contracts have no provider SDK dependency.
- Fake provider failures and timeouts terminate in a bounded, redacted form.
- Full Ruff, mypy strict, pytest, TypeScript strict and security checks pass.

## Required stop

After publication and GitHub Actions, stop at `NEEDS_HUMAN_PHASE_3C_REVIEW`.
