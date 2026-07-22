# Decision 0004 — Phase 3C hardens contracts without creating a second runtime

- Status: accepted
- Date: 2026-07-21
- Authority: explicit Phase 3C human approval and the v1.0 duplex specification

## Decision

Phase 3C builds only provider-free boundaries and deterministic tests. The duplex harness is not a
conversation orchestrator or deployable runtime. It exists to prove input/output queue independence
and the final Generation Guard admission invariant.

Protocol, provider and transport contracts contain no LINE, MiniMax, Deepgram, LLM, LiveKit or
Pipecat SDK calls. Test fakes remain labelled as synthetic evidence and cannot establish real
provider behavior.

## Audio and generation ownership

- Input is PCM16LE, 16 kHz, mono, 20 ms for the direct LIFF boundary proposal.
- Formal MiniMax output remains verified MP3, 24 kHz, mono.
- Compressed output duration is supplied only after an authorized decoder boundary; Phase 3C uses
  declared synthetic durations and does not claim MP3 timing discovery.
- Every output chunk carries a GenerationToken and is checked immediately before playback.
- Local interruption does not claim provider-side cancellation or billing termination.

## Configuration conflict resolution

The historical infrastructure guide recommends hard-coded Voice IDs. The governing PLM
specification forbids this. Voice IDs remain environment/Secret-Manager-only and persona-scoped.

## Stop

No external database execution, formal MiniMax service, Pipecat Pipeline, LINE activation,
LiveKit, real owner data or production deployment is authorized. The milestone stops at
`NEEDS_HUMAN_PHASE_3C_REVIEW` after publication and CI.
