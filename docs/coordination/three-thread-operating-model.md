# Three-Thread Operating Model

## Purpose

The Xie Wenxian Holy Grail 3.0 project uses three deliberately separated Codex threads. Conversation
history is not shared automatically. Git, versioned coordination records and explicit thread
messages are the only authoritative handoff mechanisms.

## Roles

### Command Center

- Owns prioritization, milestone authority, cross-thread dispatch and final acceptance.
- May read A/B status and send bounded missions or handoff summaries.
- Does not silently broaden a mission or treat another thread's inference as approval.

### Thread A — Engineering Runtime

- Owns application code, infrastructure, CI, identity isolation, transport and deployment contracts.
- Must not author persona claims, owner quotes or release-persona content.
- Current checkout: `C:\Users\waiti\PLM`.

### Thread B — Persona and Knowledge Lab

- Owns candidate classification, provenance, owner-confirmation queues, knowledge governance and
  offline persona evaluation assets.
- Must not deploy, activate providers, handle secrets or change runtime/infrastructure.
- Uses an isolated Codex worktree and dedicated branch.

## Authoritative synchronization

The synchronization order is:

1. Command Center issues a mission with allowed paths, forbidden actions, evidence and stop state.
2. The assigned thread works only in its isolated worktree and branch.
3. The thread records durable results in Git and its status envelope.
4. Command Center reads the result, checks Git/CI evidence and updates the global milestone.
5. Only cross-impact facts are sent to the other thread; no thread can command another thread.

Chat summaries are operational notifications, not the system of record. The system of record is the
canonical PLM repository, including `.loop/coordination`, `.loop/progress.json`, decisions, runs,
evidence, acceptance records, commits and pull requests.

## Path ownership

| Area | Primary writer | Other thread access |
| --- | --- | --- |
| `src/`, `web/`, `migrations/`, infrastructure and CI | A | B read-only when needed |
| `docs/persona/xiewenxian/` and future governed persona packages | B | A consumes versioned contracts only |
| `.loop/coordination/`, coordination decisions and cross-thread handoffs | Command Center | A/B read and update only their assigned status envelope |
| Raw V2 prompt and meeting record | User-owned, untracked | Read-only; never copied or committed without a separate source-governance mission |

Overlapping edits require a new Command Center decision before work begins.

## Workspace isolation

- A retains the canonical checkout and `codex/liff-staging-bootstrap` branch.
- B uses its own Codex worktree and `codex/xiewenxian-persona-lab` branch.
- Command Center uses `codex/three-thread-coordination-baseline` in a separate coordination worktree.
- The worktrees share Git objects but not working-directory state.
- Switching another thread's branch, moving untracked assets or writing outside the assigned path is
  forbidden without explicit Command Center authority.

## Status envelope

Every thread status record must include:

- thread ID and role;
- worktree and branch;
- HEAD and remote parity when a remote exists;
- mission and mission state;
- allowed and forbidden scope;
- files changed, commit, pull request and CI state;
- blockers, risks and required human action;
- explicit production, secret and external-integration state;
- next stop condition.

## Retained system boundaries

- Pipecat is the sole orchestrator.
- MiniMax remains one WebSocket session per generation.
- Generation Guard gates all text and audio output.
- LINE, microphone, WebSocket, MiniMax runtime, LiveKit, database and production remain disabled
  until separately authorized.
- Owner Evidence must never enter Student Memory.
- Tracy assets remain permanently excluded.
