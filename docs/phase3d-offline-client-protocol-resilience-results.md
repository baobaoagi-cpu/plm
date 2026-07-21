# Phase 3D — Offline Client and Protocol Resilience Results

Status: `COMPLETED / APPROVED / NEEDS_HUMAN_POST_PHASE_3D_PUBLISH_REVIEW`

## Outcome

All five offline missions passed without a credential, external connection or real user/audio
record. The work supplies integration-safe client/protocol seams; it is not a deployable call
runtime.

| Requirement | Result |
|---|---|
| PCM16LE 16 kHz mono 20 ms / 640-byte framing | VERIFIED SYNTHETIC |
| 48 kHz → 16 kHz deterministic framing | VERIFIED SYNTHETIC |
| Microphone continues while playback is queued | VERIFIED SYNTHETIC |
| Interrupt hard-clear and late-audio rejection | VERIFIED SYNTHETIC |
| Client state transitions and terminal hangup | VERIFIED |
| AEC capability observation contract | VERIFIED |
| Real browser AEC behavior/quality | UNKNOWN |
| Strict start/order/duplicate/session rules | VERIFIED |
| Stale generation commands | VERIFIED REJECTED |
| Invalid UTF-8/oversized/unknown/sensitive frames | VERIFIED REDACTED |
| Short-lived audience/purpose/session/subject grant | VERIFIED OFFLINE |
| Nonce replay and unknown/tampered key | VERIFIED_SINGLE_PROCESS_OFFLINE_ONLY / REJECTED |
| Telemetry payload/secret exclusion | VERIFIED |
| 10,000 protocol frames | PASS, replay memory retained 64 IDs |
| 1,000 fresh-grant reconnects | PASS |
| 10,000 telemetry events | PASS, retained tail 128 |
| 1,000 generation interruptions | PASS, stale playback 0 |
| Browser duplicate/regressed audio sequence | VERIFIED REJECTED |
| Architecture boundary tests | PASS, 3 |

## Validation

- Ruff: pass.
- mypy strict: pass, 85 source files.
- pytest: pass, 262 tests.
- Phase 3D focused pytest: pass, 29 tests in 0.65 seconds.
- TypeScript strict: pass.
- Browser offline executable assertions: pass, 22.
- npm dependency tree: pass; dependency and lock files unchanged.
- npm audit: inherited pass from Phase 3B because the lockfile is unchanged; no online rerun was
  performed in this offline-only phase.

## Important interpretation

The call-grant signing keys in tests are deterministic synthetic bytes. This proves token mechanics,
not key custody or production identity. The in-memory replay guard proves single use only inside a
single Python process when validators share that guard; it does not prove multi-worker,
multi-container or restart-safe replay rejection. The AudioWorklet is compiled and tested through its pure
framing boundary but is not connected to `getUserMedia`. AEC is an observed browser setting only.

## Evidence

- `.loop/evidence/phase3d-offline-client-protocol-resilience-i15.json`
- `.loop/runs/iteration-015-phase3d-offline-client-protocol-resilience.md`
- `docs/security/phase3d-offline-threat-model.md`

## Publication

- Gate DB-1 Draft PR: `https://github.com/baobaoagi-cpu/plm/pull/4`
- Phase 3D Draft PR: `https://github.com/baobaoagi-cpu/plm/pull/5`
- Stacked bases: Phase 3C → Gate DB-1 → Phase 3D
- Initial push and PR quality runs: all passed
- Merge/deployment: none

Required stop: `NEEDS_HUMAN_POST_PHASE_3D_PUBLISH_REVIEW`.
