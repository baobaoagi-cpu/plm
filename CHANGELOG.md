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

### Security

- All credentials are environment-only; `.env` and audio artifacts are ignored by Git.
- API keys, authorization headers, full Voice IDs, and synthesis text are excluded from evidence.

### Decision

- Use one WebSocket session per generation.
- Treat socket close only as an inferred cancellation layer and discard stale audio locally.
- Keep Pipecat as the sole orchestrator; the legacy pipeline remains reference-only.
- Task 003 is complete. Task 004 remains unauthorized and the post-publish stop is
  `NEEDS_HUMAN_POST_PUBLISH_REVIEW`.
