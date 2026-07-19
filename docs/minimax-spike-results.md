# MiniMax WebSocket Spike Results

## Status

Task 002 is `COMPLETED`. All three approved probes were executed sequentially, once each, with
short text and redacted evidence. The project is stopped at `NEEDS_HUMAN_MILESTONE_APPROVAL`;
Task 003 is not authorized.

## Probe 1 - Standard

- Connect latency: 937 ms
- First-audio TTFA: 3,921 ms
- Two 5-character `task_continue` messages; both produced final responses
- `task_finish` was sent before first audio; `task_finished` arrived after both queued inputs
- 24 chunks, 43,098 bytes; MP3, 24,000 Hz, mono, reported duration 1,439 ms
- `connected_success`, `task_started`, `task_finished`, provider close; all status codes 0

Conclusion: lifecycle and queue drain `VERIFIED` for this run.

Evidence: `.loop/evidence/probe-standard-i4-summary.md`

## Probe 2 - Close After First Audio

- Independent session; connect latency 1,125 ms; TTFA 718 ms
- Close initiated immediately after first audio
- Close returned about 5,016 ms later
- Eight buffered messages containing audio remained readable after close returned
- Connection then became terminal; no cancellation ACK, usage, or billing evidence

Conclusion: client termination `VERIFIED`; socket close cancellation value `INFERRED`; provider-side
compute and billing cancellation `UNKNOWN`. Local playback clear and generation discard are required.

Evidence: `.loop/evidence/probe-close-i5-summary.md`

## Probe 3 - Session Reuse

- Same connection/session; first-generation connect latency 1,047 ms and TTFA 750 ms
- First generation produced 15 chunks and 26,541 bytes
- Second `task_start` returned `task_failed`, status code 2206
- No second-generation audio or TTFA; no retry or bypass

Conclusion: same-session second generation `REJECTED`; use `ONE_SESSION_PER_GENERATION`.

Evidence: `.loop/evidence/probe-reuse-i6-summary.md`

## Offline decode

The complete Standard MP3 and its first 2,048-byte chunk were decoded with `miniaudio.mp3_read_s16`.
The first chunk yielded 1,775 frames at 24 kHz mono, so single-chunk decodability is `VERIFIED`.

Evidence: `.loop/evidence/offline-mp3-decode-i6.json`

## Final decision matrix

| Requirement | Result |
|---|---|
| WebSocket endpoint | `VERIFIED` |
| Authorization | `VERIFIED` |
| connected_success | `VERIFIED` |
| task_start | `VERIFIED` |
| multiple task_continue | `VERIFIED` |
| task_finish | `VERIFIED` |
| audio event schema | `VERIFIED` |
| audio encoding | `VERIFIED` - MP3 |
| sample rate | `VERIFIED` - 24,000 Hz |
| channel count | `VERIFIED` - mono |
| single chunk decodable | `VERIFIED` |
| first audio TTFA | Standard 3,921 ms; Close 718 ms; Reuse first generation 750 ms |
| task_finish queue behavior | `VERIFIED` |
| socket close cancellation value | `INFERRED` |
| same-session second generation | `REJECTED` |
| connection strategy | `ONE_SESSION_PER_GENERATION` |

No claim is made that closing the socket stops MiniMax server-side computation or billing.
