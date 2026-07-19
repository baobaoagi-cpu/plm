# Blockers

## B-003 - Legacy extraction authority

- Status: `RESOLVED_FOR_REPOSITORY_MIGRATION_REPAIR_ONLY`
- Allowed: backend-free, call-disabled shell rewritten in PLM.
- Still blocked: LIFF SDK identity, audio hooks, WebSocket protocol, backend/provider integration.

## B-004 - Task 005 milestone authority

- Status: `NOT_AUTHORIZED`
- Blocks: formal MiniMax TTS service, Pipecat pipeline, LiveKit transport and LINE OA integration.
- Resolution: separate human milestone approval after migration review.

## B-005 - Owner consent and release authority

- Status: `INCOMPLETE`
- Blocks: Owner Confirmation evidence upgrade, raw V2 publication, Voice ID use, account delivery,
  Mem0, recordings, public/production use and release persona.
- Resolution: owner consent checklist plus governance approval.

## Retained hard constraints

- PLM is canonical; holygrail2 is provenance only.
- Pipecat remains the sole orchestrator.
- MiniMax remains one WebSocket session per generation.
- Generation Guard cannot be bypassed.
- Raw V2 remains `REFERENCE_ONLY`; 46 candidates remain engineering interpretations.
