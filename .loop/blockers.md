# Blockers

## B-003 - Legacy extraction authority

- Status: `NOT_AUTHORIZED`
- Blocks: every extraction, copy, adapter, protocol implementation and integration action.
- Resolution: human selects/approves one extraction stage and its exact file scope.

## B-004 - Task 005 milestone authority

- Status: `NEEDS_HUMAN_MILESTONE_APPROVAL`
- Blocks: Task 005, formal MiniMax TTS service, Pipecat pipeline, LiveKit transport and LINE OA
  integration.
- Resolution: human reviews Task 004 evidence and explicitly authorizes the next bounded milestone.

## Retained hard constraints

- Task 004 is `COMPLETED`; Task 005 remains `NOT_AUTHORIZED`.
- Legacy MiniMax pooling is deprecated; formal strategy remains one session per generation.
- Legacy frontend mic gating must not be ported.
- Legacy VoicePipeline must not become a second orchestrator.
- Production env values must not be copied or recorded.
