# Blockers

## B-003 - Legacy extraction authority

- Status: `RESOLVED_FOR_OFFLINE_PROTOCOL_CONTRACTS_ONLY`
- Allowed: backend-free, call-disabled shell rewritten in PLM.
- Also allowed: Phase 3C provider-free Protocol v1 and synthetic audio contracts.
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

## Retained hard constraints

- PLM is canonical; holygrail2 is provenance only.
- Pipecat remains the sole orchestrator.
- MiniMax remains one WebSocket session per generation.
- Generation Guard cannot be bypassed.
- Raw V2 remains `REFERENCE_ONLY`; 46 candidates remain engineering interpretations.
- Phase 3B accepts synthetic data only and cannot publish or create a release persona.
