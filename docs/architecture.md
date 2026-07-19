# Architecture

Pipecat is the sole orchestration layer. LiveKit is the bidirectional WebRTC media layer,
and MiniMax WebSocket TTS is the sole production voice output. STT and LLM providers remain
behind replaceable streaming interfaces.

Detailed implementation decisions remain in `minimax-duplex-voice-spec-v1.0.md` until their
respective milestones are implemented and verified.

The proposed LINE OA / LIFF integration boundary and extraction gates are documented in
`docs/line-oa-voice-call-integration-blueprint.md`. It is a design artifact only; it does not
authorize Task 004 or make the legacy package part of the runtime.
