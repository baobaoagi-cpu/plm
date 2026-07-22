# Decision 0007 — Three-Thread Coordination and Worktree Isolation

## Status

`APPROVED / IMPLEMENTED_LOCALLY / NEEDS_HUMAN_THREE_THREAD_BASELINE_REVIEW`

## Decision

The current conversation is the Command Center. Thread A is the Engineering Runtime. Thread B is
the Persona and Knowledge Lab. Conversation memory is not assumed to be shared. The Command Center
coordinates through explicit Codex thread messages and versioned PLM records.

Thread A retains the canonical checkout. Thread B receives a separate Codex worktree and dedicated
persona branch. The Command Center maintains this baseline on a separate coordination branch.

## Constraints

- A and B may not command one another.
- A may not author persona content.
- B may not alter runtime, infrastructure or deployment.
- Raw user-owned source files remain untracked at their original PLM paths.
- No production, external integration, release persona or provider use is authorized.
- A mission that overlaps path ownership requires a new Command Center decision.

## Evidence

- A worktree: `C:\Users\waiti\PLM`, branch `codex/liff-staging-bootstrap`.
- B worktree: `C:\Users\waiti\.codex\worktrees\0408\PLM`, branch
  `codex/xiewenxian-persona-lab`.
- Command Center worktree: `C:\tmp\plm-three-thread-coordination`, branch
  `codex/three-thread-coordination-baseline`.
- `CODEX_handoff.md` and the meeting record were restored to their original untracked PLM paths
  after the worktree handoff and verified byte-for-byte by SHA-256. The ignored raw V2 prompt stayed
  at its original PLM path throughout.

## Stop

`NEEDS_HUMAN_THREE_THREAD_BASELINE_REVIEW`
