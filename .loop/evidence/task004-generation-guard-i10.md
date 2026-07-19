# Task 004 Generation Guard Evidence

## Scope

Implemented a provider-, transport- and orchestrator-independent Generation Guard Core. No network,
MiniMax provider, Pipecat, LiveKit, LINE OA or Legacy package code was called or imported.

## Verified capabilities

- Seven-state lifecycle with a mechanical transition table and terminal-state permanence.
- Collision-safe UUID generation IDs and per-session monotonic sequences.
- At most one active generation per session, with atomic supersession before replacement.
- Local cancellation lifecycle supports `ACTIVE → CANCELLING → CANCELLED`.
- `should_accept` fails closed without throwing for terminal, stale, unknown or mismatched tokens.
- `assert_accepting` provides typed diagnostic errors without metadata.
- Thread-safe short critical sections use an instance-owned `threading.RLock`; event sinks run after
  lock release and no external I/O occurs inside the lock.
- Explicit TTL/cutoff and count-bounded cleanup deletes terminal records only.
- Snapshot hashes session IDs and omits metadata; accepted metadata is shallow JSON scalar data with
  restricted keys and lengths.

## Verification iterations

### Build iteration 1

- pytest: 107 passed.
- Ruff: two mechanical findings (line length and StrEnum modernization).
- mypy: one test-helper return typing finding.

### Build iteration 2

- Ruff: PASS.
- mypy strict: PASS for the Task 004 scope; the final full-project gate passed 51 project files.
- pytest: PASS, 107 tests.
- Existing Task 001–003 tests: PASS with no fixture or protocol-model changes.
- One non-failing sandbox warning remained because pytest could not write `.pytest_cache`; all
  collection, execution and assertions completed.

## Concurrency and late-data evidence

- Two worker threads raced `cancel` against `complete`; exactly one terminal transition won.
- Twenty worker threads concurrently replaced one session; exactly one generation remained active
  and nineteen returned tokens were superseded.
- One hundred simulated late audio chunks were rejected without exceptions.
- Event sink re-entered the guard from a separate thread, proving it was invoked outside the lock.

## Security and boundaries

- Snapshot/event JSON contains no metadata or raw session ID.
- API key, Voice ID, authorization, prompt/text/transcript/audio/token/secret metadata keys are
  rejected.
- Forbidden runtime imports test covers Pipecat, LiveKit, WebSockets, LINE and Task 003 protocol.
- Provider API calls: 0.

Result: `COMPLETED`

Stop: `NEEDS_HUMAN_MILESTONE_APPROVAL`.
