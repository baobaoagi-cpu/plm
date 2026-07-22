# Changelog

## [Unreleased]

### Added

- Offline-only LIFF identity activation seams: official npm SDK adapter with missing-config gating,
  openid-only token handoff, LINE v2.1 verify request/response contract, safe issuer/audience/expiry/
  subject validation, and direct reuse of the Phase 3B tenant-bound identity mapper.
- LIFF identity security lint, backend failure/redaction tests, frontend failure-gating tests,
  screenshot-evidence mapping, threat model and future human application checklist.

- Public, machine-readable LIFF staging registration contract and redacted anonymous network
  evidence. The LIFF ID, LIFF URL and endpoint are classified as public configuration while LINE
  identity, scopes and all runtime integrations remain unverified or disabled.

- Backend-free, call-disabled LIFF staging entrypoint, fail-closed static server, restrictive
  browser security headers, dedicated Railway staging service and verified public HTTPS endpoint.

- Railway config-as-code and a fail-closed, dependency-free staging health shell that binds the
  assigned port while refusing production and all external integrations.
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
- Gate DB-1 reproducible PostgreSQL 15 harness with a network-disabled tmpfs container, synthetic
  RLS scenarios, provider-role checks, guarded rollback proof and guaranteed cleanup.
- Phase 3D offline browser PCM framer, AudioWorklet contract, duplex lab and explicit call-state
  machine with hard interruption/hangup cleanup.
- Short-lived session/subject-bound call grants, bounded nonce replay defense, strict Protocol v1
  ingress ordering and redacted bounded telemetry/latency contracts.
- Deterministic resilience soak covering 10,000 frames, 1,000 reconnects, 10,000 events and 1,000
  interrupted generations without provider or network access.

### Security

- LINE ID tokens and raw subjects are redacted from repr/events/responses and never persisted;
  client-decoded claims are rejected as a trust source, and identity failure cannot enable calls,
  microphone, WebSocket or AI capabilities.
- All credentials are environment-only; `.env` and audio artifacts are ignored by Git.
- API keys, authorization headers, full Voice IDs, and synthesis text are excluded from evidence.
- Phase 3B migration reruns now set the fixed staging tenant only with transaction-local scope, so
  an already-forced RLS policy cannot reject the idempotent tenant seed or leak context.
- Gate DB-1 now qualifies outer RLS references explicitly, directly tests a known foreign
  principal ID and pins its disposable PostgreSQL image by digest.
- Browser playback rejects duplicate or regressed audio sequence numbers within a generation; CI
  now executes the offline browser assertion suite.
- Call-grant nonce replay protection is explicitly classified as
  `VERIFIED_SINGLE_PROCESS_OFFLINE_ONLY`; distributed and restart-safe enforcement remains unknown.

### Decision

- LIFF Console settings are human-screenshot verified as openid-only with profile, chat message,
  Add friend, QR, Module mode and share target picker disabled. Implementation remains offline-only;
  Railway, real login and LINE transport are unchanged and require a separate gate.
- Public LIFF registration is verified only through anonymous HTTP and static redirect evidence.
  It does not prove LINE identity or scopes, does not inject the LIFF ID into Railway/runtime
  configuration, and stops at `NEEDS_HUMAN_LIFF_IDENTITY_ACTIVATION_REVIEW`.
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
- Gate DB-1 verifies local PostgreSQL enforcement only and stops at
  `NEEDS_HUMAN_GATE_DB1_REVIEW`; external staging and production remain disconnected.
- Phase 3D proves only offline client/protocol mechanics. Real browser, LIFF, WebSocket, provider,
  transport and production behavior remain unverified; stop at `NEEDS_HUMAN_PHASE_3D_REVIEW`.
- Railway deployment readiness is limited to a health-only staging shell. It adds no formal voice
  runtime or external integration and must stop at `NEEDS_HUMAN_STAGING_DEPLOYMENT_REVIEW`.
- Human Phase 3D review is approved. Gate DB-1 and Phase 3D are published as stacked Draft PRs #4
  and #5 with initial GitHub Actions passing; neither is merged or deployed. The current stop is
  `NEEDS_HUMAN_FINAL_MERGE_REVIEW` after the approved review repair and passing Actions.
