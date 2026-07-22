# Current Milestone Plan

## Milestone

`Phase 3C — Offline Duplex Architecture Hardening`

## Goal

Lock the configuration, protocol, lease, audio queue, generation and provider-adapter boundaries
before any real staging credential is used.

## Delivered locally

- Machine-readable environment contract with offline fail-closed defaults.
- Strict Protocol v1 client/server schemas and bounded parser.
- Stale-safe per-principal Session Registry.
- Independent bounded microphone and generation-scoped playback queues.
- Offline duplex harness with interruption, hangup, backpressure and race proofs.
- Provider-neutral STT, LLM, TTS, identity and transport contracts.
- Reusable deterministic fakes and bounded provider error/timeout mapping.

## Validation complete

- Final full regression, architecture-boundary, dependency-integrity and security scans passed.
- Evidence hashes and iteration record are committed.
- Phase 3C branch and Draft PR #3 are published; both GitHub Actions quality runs passed.

## Pending human action

- Human Phase 3C review.

## Explicitly not delivered

- Local or external PostgreSQL execution.
- Formal MiniMaxTTSService or any provider connection.
- Pipecat Pipeline, LINE activation, LIFF identity SDK or LiveKit integration.
- Real identity, owner/student data, Mem0, R2, audio recording or production.
- Release persona or owner-confirmed evidence.

## Required stop

`NEEDS_HUMAN_PHASE_3C_REVIEW`
