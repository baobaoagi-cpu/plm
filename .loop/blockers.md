# Blockers

## B-003 - Post-publish and extraction authority

- Status: `NEEDS_HUMAN_POST_PUBLISH_REVIEW`
- Blocks: every extraction, copy, adapter, protocol implementation and integration action.
- Resolution: human reviews the initial publication, then selects/approves one stage and its exact
  file scope.

## Retained hard constraints

- Task 004 remains `NOT_AUTHORIZED`.
- Legacy MiniMax pooling is deprecated; formal strategy remains one session per generation.
- Legacy frontend mic gating must not be ported.
- Legacy VoicePipeline must not become a second orchestrator.
- Production env values must not be copied or recorded.
