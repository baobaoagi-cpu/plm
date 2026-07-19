# Decision 0001 - Three-Loop governance and configuration priority

- Status: accepted
- Date: 2026-07-19
- Evidence state: `VERIFIED` by the user's explicit project instructions and frozen specification

## Decision

The project adopts Review, Repair, and Validate loops with repository-backed progress, evidence,
blockers, decisions, and run records. Milestones advance only through a Governance decision after
their acceptance gates pass.

When instructions conflict, use this priority:

1. Latest explicit human instruction
2. Frozen project specification and architecture decisions
3. Milestone plan
4. AGENTS.md working rules
5. Progress and run records
6. Historical code conventions

## Configuration conflict resolved

The infrastructure reference contains a historical recommendation to hard-code MiniMax Voice IDs.
The current project specification and the user's latest instruction explicitly require every secret
and Voice ID to come from environment variables. Therefore this project must not hard-code a Voice
ID. The specification wins by documented priority.

## Architecture boundary

Pipecat remains the sole orchestration core. LiveKit remains a Pipecat WebRTC transport only, and
MiniMax WebSocket TTS remains the sole production voice output. This governance change does not
authorize implementation beyond Task 002.

