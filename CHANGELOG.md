# Changelog

## [Unreleased]

### Added

- Python 3.12/uv project skeleton with Ruff, mypy strict, pytest, CI, Docker, and deployment stubs.
- Independent MiniMax WebSocket spike with redacted timelines, timing metrics, streamed audio capture,
  Standard, close-after-first-audio, and session-reuse modes.
- Authenticated Task 002 evidence for MP3 24 kHz mono output, queue draining, cancellation behavior,
  single-chunk decoding, and same-session reuse rejection.
- Pure MiniMax protocol layer with typed outbound/inbound events, strict parser, verified hex audio
  decoder, status-2206 reuse error mapping, redaction helpers, and synthetic fixtures.
- Read-only Legacy Voice Call Feature Extraction Audit covering all 43 reference files, WebSocket
  protocol, audio lifecycle, reuse classifications, security findings and staged extraction plan.
- LINE OA / LIFF integration blueprint covering authenticated identity, versioned WebSocket
  contracts, continuous audio, generation-safe interruption, deployment boundaries and staged
  release gates without importing the legacy runtime.
- Provider-independent, thread-safe Generation Guard with explicit lifecycle transitions,
  per-session active ownership, terminal late-data rejection, atomic replacement/cancellation,
  bounded terminal cleanup, redacted snapshots and structured state-change events.
- PLM-canonical 謝文憲 Phase 2 candidate register、Owner Confirmation Queue、來源／衝突治理資產。
- PLM-native Owner Calibration 3A identity policy：專屬 tenant、persona、Mem0 reservation、
  LINE／Voice slots、storage namespaces、allowlist、Sandbox notice 與 fail-closed kill switch。
- Backend-free、預設停用的謝文憲 LIFF call shell、mic permission、waveform 與 dial tone；未搬
  legacy audio/WebSocket hooks、persona assets 或第二套編排器。
- Repository Migration inventory/report、V2 custody review、隔離／污染測試與 Web strict CI。
- Phase 3B verified-identity mapper、SHA-256 effective user IDs、synthetic-only isolation store、
  fail-closed candidate persona loader 與四個 immutable read-only admin contracts。
- PostgreSQL 15+ `xiewenxian_staging` migration contract，包含 composite tenant/principal foreign
  keys、forced RLS、indexed filters、provider-role guards、least privilege 與 staging-only rollback。
- Dev-only PostgreSQL AST parser pinned in CI so both migration directions are syntax-checked on
  every quality run.
- Phase 3C fail-closed environment contract with exact `.env.example` parity, secret/public value
  classification, immutable one-session-per-generation and stale-discard policies.
- Strict Protocol v1 client/server schemas, bounded redacted parser and stale-safe per-principal
  transport lease registry.
- Independent bounded input/output audio queues and an offline duplex harness with pre-playback
  Generation Guard enforcement, backpressure, idempotent hangup and deterministic race proofs.
- Provider-neutral STT, LLM, generation-scoped TTS, identity-verification and transport contracts,
  plus reusable synthetic fakes and bounded redacted timeout/error mapping.

### Security

- All credentials are environment-only; `.env` and audio artifacts are ignored by Git.
- API keys, authorization headers, full Voice IDs, and synthesis text are excluded from evidence.

### Decision

- Use one WebSocket session per generation.
- Treat socket close only as an inferred cancellation layer and discard stale audio locally.
- Keep Pipecat as the sole orchestrator; the legacy pipeline remains reference-only.
- Task 003 and the public initial publish are complete.
- Task 004 is complete. Task 005 and LINE OA integration remain unauthorized. Repository Migration
  Repair was followed by a separately authorized Phase 3B staging proof; the current stop is
  `NEEDS_HUMAN_PHASE_3B_REVIEW`.
- `baobaoagi-cpu/plm` is the sole canonical repository for the Xie Wenxian system. The historical
  holygrail2 branch is provenance only and was not modified or deleted.
- Phase 3B is staging proof only. No external database was contacted, no real identity/data was
  used, and the required stop is `NEEDS_HUMAN_PHASE_3B_REVIEW`.
- Phase 3C is offline hardening only. It creates no MiniMaxTTSService, Pipecat Pipeline, LINE or
  LiveKit integration and stops at `NEEDS_HUMAN_PHASE_3C_REVIEW` after CI.
