# Blockers

## B-003 - Legacy extraction authority

- Status: `RESOLVED_FOR_OFFLINE_PROTOCOL_CONTRACTS_ONLY`
- Allowed: backend-free, call-disabled shell rewritten in PLM.
- Also allowed: Phase 3C provider-free Protocol v1 and synthetic audio contracts, plus Phase 3D
  offline browser, grant, replay, telemetry and soak contracts.
- Still blocked: LIFF SDK identity, real audio hooks, WebSocket server, backend/provider integration.

## B-004 - Task 005 milestone authority

- Status: `NOT_AUTHORIZED`
- Blocks: formal MiniMax TTS service, Pipecat pipeline, LiveKit transport and LINE OA integration.
- Resolution: separate human milestone approval after migration review.

## B-005 - Owner consent and release authority

- Status: `INCOMPLETE`
- Blocks: Owner Confirmation evidence upgrade, raw V2 publication, Voice ID use, account delivery,
  Mem0, recordings, public/production use and release persona.
- Resolution: owner consent checklist plus governance approval.

## B-006 - External staging database identity

- Status: `LOCAL_RLS_PROOF_RESOLVED / EXTERNAL_NOT_CONFIGURED_OR_CONTACTED`
- Gate DB-1 executed the Phase 3B migration twice on disposable PostgreSQL 15.18 and verified
  forced RLS, roles, data-class separation and guarded rollback with synthetic data.
- Blocks: external staging migration, persistence integration, connection-pool context reset and
  live admin database reads.
- Resolution: human supplies a dedicated staging DB identity, approved application roles, retention
  policy and rollback window in a later milestone. Production credentials are never acceptable.

## B-007 - External staging provider identities

- Status: `NOT_CONFIGURED / NOT_CONTACTED`
- Phase 3C defines slots and adapter contracts only.
- Blocks: real LINE verification, STT/LLM calls, formal MiniMax voice runtime and LiveKit transport.
- Resolution: human supplies persona/environment-isolated staging identities and separately approves
  the corresponding integration milestone. Populating a secret does not activate an integration.

## B-008 - Real browser and transport proof

- Status: `NOT_AUTHORIZED / NOT_EXECUTED`
- Phase 3D compiles an AudioWorklet and proves pure client/protocol logic only.
- Blocks: `getUserMedia`, real device sample-rate/AEC tests, LIFF SDK, WebSocket transport, network
  chaos and end-to-end duplex latency.
- Resolution: dedicated staging identities, real-device test consent and a separately approved
  integration milestone. Offline AEC observation must not be described as real AEC quality.

## Retained hard constraints

- PLM is canonical; holygrail2 is provenance only.
- Pipecat remains the sole orchestrator.
- MiniMax remains one WebSocket session per generation.
- Generation Guard cannot be bypassed.
- Raw V2 remains `REFERENCE_ONLY`; 46 candidates remain engineering interpretations.
- Phase 3B accepts synthetic data only and cannot publish or create a release persona.

## B-009 - Distributed call-grant replay protection

- Status: `VERIFIED_SINGLE_PROCESS_OFFLINE_ONLY / DISTRIBUTED_UNKNOWN`
- The bounded in-memory nonce guard rejects replay only when validators share the same guard in one
  Python process. It is not durable across worker processes, containers or restarts.
- Blocks: any multi-worker or horizontally scaled real transport milestone.
- Resolution: provide an atomic shared nonce store, or prove and enforce a single-instance runtime,
  under a separately authorized milestone. This repair does not start Phase 3E.

## B-010 - Railway GitHub source authorization

- Status: `BLOCKED_REPO_SOURCE_UNAUTHORIZED`
- Railway account authentication, staging environment creation, CLI upload deployment and public
  health verification all succeeded.
- Attaching `baobaoagi-cpu/plm` as the staging service GitHub source returned `Unauthorized` and was
  not retried or bypassed.
- Blocks: the claim that a GitHub branch push automatically deploys to Railway staging.
- Resolution: a human grants the Railway GitHub integration access to `baobaoagi-cpu/plm` and
  connects `plm-staging-readiness` to `codex/railway-staging-readiness`.

## B-011 - LIFF app creation and identity activation

- Status: `SHELL_DEPLOYED / NEEDS_HUMAN_LIFF_APP_CREATION`
- The backend-free, call-disabled staging shell is publicly reachable over HTTPS.
- Blocks: a LIFF ID, LIFF SDK initialization, LINE identity verification, microphone permission,
  WebSocket transport and any real call.
- Resolution: a human creates the LIFF app in the dedicated LINE Login channel using the documented
  endpoint. Activating identity or any integration remains a separate milestone.

## B-012 - Meeting record primary-media verification and consent

- Status: `E0_SUMMARY_UNVERIFIED / NEEDS_HUMAN_SOURCE_REVIEW`
- The registered DOCX is an automated-transcript-derived summary, not a speaker/timecode verified
  transcript. It explicitly warns that names, dates, amounts and specialist terms may be inaccurate.
- Blocks: populating `owner_quote`, upgrading any attributed claim to owner-confirmed evidence,
  publishing biographical/family details, or treating public media as authorized voice/knowledge data.
- Resolution: approve source custody and consent, map claims to primary recording timestamps, verify
  exact wording and third-party privacy, and complete source-by-source rights review.
