# Phase 3C Offline Duplex Architecture Hardening Results

Status: `COMPLETED / NEEDS_HUMAN_PHASE_3C_REVIEW`

## Mission results

### Mission 1 — Configuration

- Complete `.env.example` to machine-readable environment-name parity.
- Secret, sensitive, server and public-browser value classes are disjoint.
- Offline defaults require sandbox mode and kill switch, and reject all external integration flags.
- MP3 24 kHz mono, one-session-per-generation, Generation Guard and stale discard are immutable.
- Diagnostic snapshots include no secret values.

### Mission 2 — Protocol and leases

- Six strict client frame models and nine server frame models use protocol version 1.
- Unknown/extra fields, untrusted client identity, invalid audio negotiation and oversized frames
  fail closed with safe errors.
- One effective principal owns one current transport lease; reconnect supersedes the old lease.
- Exact-token release makes stale cleanup unable to remove a newer lease.

### Mission 3 — Offline duplex proof

- PCM16LE 16 kHz mono input frames and verified MiniMax MP3 24 kHz mono output are explicit
  boundaries.
- Input and output queues have separate duration limits and backpressure counters.
- Generation is checked on enqueue and again immediately before playback.
- 40 concurrent output producers racing one interrupt: zero stale chunks returned for playback.
- 100 sequential interruption cycles: zero stale chunks returned for playback.
- Hangup clears both queues and is idempotent.

These are deterministic offline engineering proofs. They do not prove browser AEC, real network
timing, provider cancellation, Pipecat orchestration or end-to-end audio quality.

### Mission 4 — Adapter and fault contracts

- Streaming STT supports revisions and never pauses as a consequence of output state.
- Streaming LLM separates display/speak deltas and has a provider-independent cancellation token.
- TTS contract is generation-scoped and cannot reuse the fake connection for a second generation.
- Identity verification is a required contract before Phase 3B identity mapping.
- Transport contract owns media operations only and has no dialogue-state method.
- Fake connect stalls, connect failures, mid-stream failures, cancellation and late TTS audio are
  bounded and redacted.

## Validation

- Ruff: `PASS`
- mypy strict: `PASS` (79 source files)
- pytest: `PASS` (232)
- TypeScript strict: `PASS`
- Architecture boundary tests: `PASS` (3)
- npm dependency tree: `PASS`
- npm audit: `PASS_INHERITED_UNCHANGED_LOCKFILE_FROM_PHASE_3B`; no dependency or lockfile changed,
  and an online rerun was not permitted by the offline-only milestone boundary.
- Secret / forbidden runtime / Git diff checks: `PASS`
- External/provider/database calls: `0`
- Real identities/audio/transcripts: `0`
- Paid API cost: `USD 0.00`
- Final local validation elapsed: `10,492 ms`
- GitHub Actions: `PASS` (push and pull-request quality runs)
- Draft PR: `https://github.com/baobaoagi-cpu/plm/pull/3`

Final counts and hashes are recorded in `.loop/evidence/phase3c-offline-duplex-i13.json`.
