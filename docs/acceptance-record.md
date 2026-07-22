# Acceptance Record

## Task 001 - Project skeleton

- Status: `COMPLETED` (2026-07-19)
- Python 3.12, uv lock, Ruff, mypy strict, pytest/pytest-asyncio, required directories, CI
- Pipecat remains the declared sole orchestration core; no production pipeline was implemented

## Task 002 - MiniMax WebSocket Spike

- Status: `COMPLETED` (2026-07-19)
- Provider calls: 3/3 approved bounded probes used; actual real-time cost unavailable
- Standard: PASS; two `task_continue`, `task_finish`, 24 chunks, 43,098 bytes, TTFA 3,921 ms
- Close: PASS with eight late buffered audio messages; cancellation value `INFERRED`
- Reuse: second same-session `task_start` `REJECTED` with status 2206
- Connection strategy: `ONE_SESSION_PER_GENERATION`
- Audio: MP3, 24 kHz, mono; full stream and first chunk independently decoded
- Secrets: environment-only; `.env` ignored; evidence and logs redacted
- Task 003: `NOT_AUTHORIZED`
- Project state: `NEEDS_HUMAN_MILESTONE_APPROVAL`

Final lint, strict typecheck, unit tests, JSON validation, architecture check, and secret scan are
recorded in `.loop/runs/iteration-006-reuse-and-final.md`.

## Task 003 - MiniMax Protocol Models

- Status: `COMPLETED` (2026-07-19)
- Scope: pure typed protocol models, parser, verified hex payload decoder, error taxonomy,
  redaction, synthetic fixtures, and unit tests
- Status 2206: mapped to `MiniMaxUnsupportedReuseError`
- Unknown events: typed redacted fallback
- Fixtures: 7 valid synthetic JSON files with no credentials or raw provider payloads
- Ruff: PASS
- mypy strict: PASS, 48 source files
- Unit tests: PASS, 47/47 (30 Task 003 plus 17 regressions)
- Provider API calls: 0
- Forbidden implementations: none introduced
- Task 004: `NOT_AUTHORIZED`
- Project state: `NEEDS_HUMAN_MILESTONE_APPROVAL`
# Acceptance Record

## Task 004 — Generation Guard

- Status: `COMPLETED`
- Explicit lifecycle and mechanical transition table: `PASS`
- At most one active generation per session: `PASS`
- Terminal generation permanently rejects late data: `PASS`
- Unknown and mismatched tokens fail closed: `PASS`
- Cancel/complete concurrency and 20-way replacement: `PASS`
- 100 late chunks dropped without exception: `PASS`
- Terminal cleanup and active-record preservation: `PASS`
- Metadata restrictions, redacted snapshot and safe event projection: `PASS`
- Event sink called outside lock: `PASS`
- Forbidden runtime imports: `NONE`
- Ruff: `PASS`
- mypy strict: `PASS` (51 project files)
- pytest: `PASS` (107 tests)
- Paid provider calls: `0`
- Task 005 started: `NO`
- Stop condition: `NEEDS_HUMAN_MILESTONE_APPROVAL`

## GitHub initial publish and LINE OA integration design

- Integration blueprint: `DESIGN_COMPLETE_NOT_IMPLEMENTED`
- Pipecat sole orchestration boundary: `PRESERVED`
- Legacy runtime copied into PLM: `NO`
- Task 004 started: `NO`
- Public secret scan: `PASS`
- Ruff: `PASS`
- mypy strict: `PASS` (41 source files)
- pytest: `PASS` (47 tests)
- Stop condition: `NEEDS_HUMAN_POST_PUBLISH_REVIEW`

## Repository Migration Repair — 謝文憲 Phase 2／3A → PLM

- Status: `COMPLETED / NEEDS_HUMAN_PLM_MIGRATION_REVIEW`
- Canonical repository: `baobaoagi-cpu/plm`
- Historical source: `baobaoagi-cpu/holygrail2@a1ad3825cf17935622c158795dee019be99bcaaa`
- Source inventory: `PASS`，31 entries，六種分類均受支援
- Phase 2 candidates: `PASS`，46 candidate，0 owner quotes，runtime/production false
- Owner Confirmation Queue: `PASS`，15 pending，0 decisions
- Raw V2: `REFERENCE_ONLY`，27,291 bytes，SHA-256 已驗證，Git ignored
- Phase 3A identity isolation: `PASS`，PLM-native module，預設停用／kill switch 開啟
- Tenant／Persona／Mem0／LINE／Voice／DB／storage／cache／session isolation: `PASS`
- Legacy second orchestrator / connection pool imported: `NO`
- Generation Guard modified or bypassed: `NO`
- LIFF shell: `TYPECHECK_PASS / CALL_DISABLED / BACKEND_FREE`
- Ruff: `PASS`
- mypy strict: `PASS`（55 source files）
- pytest: `PASS`（126 tests）
- npm audit: `PASS`（0 vulnerabilities）
- TypeScript strict: `PASS`
- Secret scan: `PASS`（tracked diff 與 raw V2 均為 0 high-confidence matches）
- Forbidden import / Tracy contamination scans: `PASS`（production code 0 matches）
- JSON parse / Git diff check: `PASS`
- GitHub Actions: `PASS`
- Draft PR: `https://github.com/baobaoagi-cpu/plm/pull/1`
- Production connections or paid provider calls: `0`
- Release persona created: `NO`
- Stop condition: `NEEDS_HUMAN_PLM_MIGRATION_REVIEW`

## Phase 3B — Staging Identity and Data-Isolation Proof

- Status: `COMPLETED / NEEDS_HUMAN_PHASE_3B_REVIEW`
- Tenant: `xie_wenxian` only
- Environment: `staging` only
- Real LINE／Partner verification called: `NO`
- Raw external IDs persisted or logged: `NO`
- Synthetic student A/B conversation isolation: `PASS`
- Synthetic student A/B memory isolation: `PASS`
- Synthetic student A/B prompt-log isolation: `PASS`
- Owner Evidence → Student Memory hard rejection: `PASS`
- Candidate persona loader hash/governance fail-closed: `PASS`
- Read-only admin contracts: `PASS`（4 routes, GET-only, no mutation/publish）
- PostgreSQL migration AST parse: `PASS`（up/down）
- PostgreSQL migration contract tests: `PASS`
- External staging DB migration applied: `NO / NOT_AUTHORIZED_WITHOUT_DB_IDENTITY`
- Ruff: `PASS`
- mypy strict: `PASS`（63 source files）
- pytest: `PASS`（167 tests）
- TypeScript strict: `PASS`
- npm audit: `PASS`（0 vulnerabilities）
- Secret / forbidden import / Tracy contamination scans: `PASS`
- Git diff / JSON parse checks: `PASS`
- GitHub Actions: `PASS`
- Draft PR: `https://github.com/baobaoagi-cpu/plm/pull/2`
- Production connections or paid provider calls: `0`
- Pipecat／Generation Guard modified: `NO`
- Release persona created: `NO`
- Stop condition: `NEEDS_HUMAN_PHASE_3B_REVIEW`

## Phase 3C — Offline Duplex Architecture Hardening

- Status: `COMPLETED / NEEDS_HUMAN_PHASE_3C_REVIEW`
- Authorized offline missions completed: `4/4`
- `.env.example` / machine-readable contract parity: `PASS`
- Offline external integrations fail closed: `PASS`
- Production / disabled guard / connection pool / stale playback rejected: `PASS`
- Strict client protocol frames: `PASS` (6)
- Strict server protocol frames: `PASS` (9)
- Oversized / unknown / extra identity fields rejected safely: `PASS`
- Stale lease cleanup cannot remove reconnect replacement: `PASS`
- Input/output queues independent and bounded: `PASS`
- 40-way enqueue/interrupt race stale playback: `0`
- 100 sequential interruption stale playback: `0`
- Provider-neutral adapter contracts and deterministic fakes: `PASS`
- Provider timeout and mid-stream fault termination: `PASS`
- Architecture boundary tests: `PASS` (3)
- npm dependency tree: `PASS`
- JSON / Git diff / secret / forbidden-runtime / dependency-diff scans: `PASS`
- npm audit: `PASS_INHERITED_UNCHANGED_LOCKFILE_FROM_PHASE_3B` (dependency files unchanged;
  online rerun not allowed by offline milestone)
- Local/external PostgreSQL execution: `0 / SEPARATE_GATE`
- Provider/LINE/LiveKit/Mem0/R2/production connections: `0`
- Real identity/audio/transcript use: `0`
- Paid API cost: `USD 0.00`
- Ruff: `PASS`
- mypy strict: `PASS` (79 source files)
- pytest: `PASS` (232)
- TypeScript strict: `PASS`
- Final local validation elapsed: `10,492 ms`
- GitHub Actions: `PASS` (push and pull-request quality runs)
- Draft PR: `https://github.com/baobaoagi-cpu/plm/pull/3`
- Formal MiniMaxTTSService / Pipecat Pipeline created: `NO`
- Stop condition after publication: `NEEDS_HUMAN_PHASE_3C_REVIEW`

## Gate DB-1 — Local PostgreSQL RLS Execution Proof

- Status: `COMPLETED / NEEDS_HUMAN_GATE_DB1_REVIEW`
- PostgreSQL: `15.18 / VERIFIED`
- Container isolation: `network=none`, no published port, tmpfs storage
- Synthetic-only identities/data: `VERIFIED`
- Migration apply count: `2 / PASS`
- Real RLS/data-class behaviors: `15 / PASS`
- Total gate checks: `19 / PASS`
- Forced RLS tables: `6 / VERIFIED`
- Student A/B conversation, memory and prompt-log isolation: `VERIFIED`
- Owner Evidence / Student Memory separation: `VERIFIED`
- Missing identity context fail-closed: `VERIFIED`
- Table owner constrained by forced RLS: `VERIFIED`
- App/admin roles non-login, non-superuser, non-`BYPASSRLS`: `VERIFIED`
- Admin role write attempt: `REJECTED`
- Rollback without staging guard: `REJECTED / SCHEMA RETAINED`
- Rollback with staging guard: `PASS / SCHEMA REMOVED`
- Migration defect found: second apply originally failed after forced RLS
- Migration defect repaired: transaction-local fixed staging tenant context
- Acceptance threshold modified: `NO`
- External DB/provider/production connections: `0`
- Real identity/content records: `0`
- Paid API cost: `USD 0.00`
- Disposable container/data cleanup: `PASS`
- Ruff: `PASS`
- mypy strict: `PASS` (79 source files)
- pytest: `PASS` (232)
- TypeScript strict: `PASS`
- npm dependency tree: `PASS`
- JSON / Git diff / secret / forbidden-runtime scans: `PASS`
- Stop condition: `NEEDS_HUMAN_GATE_DB1_REVIEW`

## Phase 3D — Offline Client and Protocol Resilience

- Status: `COMPLETED / APPROVED / NEEDS_HUMAN_FINAL_MERGE_REVIEW`
- Authorized offline missions: `5/5`
- PCM16LE 16 kHz mono 20 ms framing: `VERIFIED SYNTHETIC`
- AudioWorklet contract compiled: `PASS / NOT CONNECTED`
- Microphone while playback queued: `VERIFIED SYNTHETIC`
- Interrupt hard-clear / late output: `PASS / REJECTED`
- Client state machine invalid transitions: `REJECTED`
- Call grant audience/purpose/session/subject/nonce/time binding: `PASS`
- Tampered, expired, replayed and wrong-scope grants:
  `VERIFIED_SINGLE_PROCESS_OFFLINE_ONLY / REJECTED`
- Protocol duplicate/reorder/gap/session/stale generation: `REJECTED`
- Invalid UTF-8/oversized/unknown/sensitive frames: `REJECTED / REDACTED`
- 10,000 protocol frames: `PASS / 64 MESSAGE IDS RETAINED`
- 1,000 fresh-grant reconnects: `PASS`
- 10,000 telemetry events: `PASS / 128 EVENTS RETAINED`
- 1,000 generation interruptions: `PASS / 0 STALE PLAYBACK`
- Ruff: `PASS`
- mypy strict: `PASS` (85 source files)
- pytest: `PASS` (262)
- Phase 3D focused tests: `PASS` (29)
- TypeScript strict: `PASS`
- Browser offline assertions: `PASS` (22)
- Browser duplicate/regressed output sequences: `REJECTED`
- Architecture boundary tests: `PASS` (3)
- npm dependency tree: `PASS`
- npm audit: `PASS_INHERITED_UNCHANGED_LOCKFILE_FROM_PHASE_3B`
- External/provider/LINE/LiveKit/database/production connections: `0`
- Real identity/audio/transcript/memory/evidence records: `0`
- Paid API cost: `USD 0.00`
- Real browser AEC, LIFF/WebSocket and provider behavior: `UNKNOWN / NOT EXECUTED`
- Gate DB-1 Draft PR: `https://github.com/baobaoagi-cpu/plm/pull/4`
- Phase 3D Draft PR: `https://github.com/baobaoagi-cpu/plm/pull/5`
- Stacked PR base/head relationships: `VERIFIED`
- Initial GitHub Actions: `PASS` (two quality runs per PR)
- Post-review GitHub Actions: `PASS` (two quality runs per PR)
- CI browser assertion execution: `VERIFIED PASS` (22)
- Initial local/remote SHA parity: `PASS`
- Merge/deployment/Phase 3E: `NO`
- Stop condition: `NEEDS_HUMAN_FINAL_MERGE_REVIEW`

## Railway Staging Deployment Readiness

- Status: `PARTIAL / NEEDS_HUMAN_RAILWAY_GITHUB_SOURCE_AUTH`
- Branch: `codex/railway-staging-readiness`
- Published commit: `ebdfcbb7efd97759abc1bd31ffe03aa20d43b4e8`
- Draft PR: `https://github.com/baobaoagi-cpu/plm/pull/6`
- GitHub Actions: `PASS_2_QUALITY_RUNS`
- Railway environment: `staging / ba28d01d-df40-4734-9cd3-ac1dbbe3a8ee`
- Railway service: `plm-staging-readiness / 6a3d2127-28cb-43f6-a950-58f5c1de2617`
- Railway deployment: `cd298968-004a-45e6-a09a-fb5aae645950 / SUCCESS`
- Public health endpoint: `VERIFIED_HTTP_200`
- Build, start, healthcheck and public networking: `VERIFIED_CLI_UPLOAD`
- GitHub source autodeploy: `BLOCKED_REPO_SOURCE_UNAUTHORIZED / NOT_VERIFIED`
- Ruff: `PASS`
- mypy strict: `PASS_87_FILES`
- pytest: `PASS_278`
- TypeScript strict: `PASS`
- Browser offline assertions: `PASS_22`
- High-confidence secret findings: `0`
- Provider/LINE/LiveKit/database/Mem0 connections: `0`
- Formal voice runtime or pipeline started: `NO`
- Production deployment changed: `NO`
- Required next action: grant Railway GitHub integration access to `baobaoagi-cpu/plm`, attach the
  staging service to `codex/railway-staging-readiness`, and verify a GitHub-triggered deployment.

## LIFF Staging Frontend Bootstrap

- Status: `COMPLETED / NEEDS_HUMAN_LIFF_APP_CREATION`
- Branch: `codex/liff-staging-bootstrap`
- Initial published commit: `eb71c4f7321e209b6c84be23ed6c1a68e8fc4325`
- Stacked Draft PR: `https://github.com/baobaoagi-cpu/plm/pull/7`
- GitHub Actions initial publish: `PASS / run 29890609272`
- Railway environment: `staging`
- Separate frontend service: `plm-liff-staging-shell / 7164b6ce-f8fa-40ae-aa0b-9114639d834a`
- Successful deployment: `d4c0d20e-d5b4-4136-9239-2d3b4a86c551`
- LIFF Endpoint URL: `https://plm-liff-staging-shell-staging.up.railway.app/`
- Public site and health endpoint: `VERIFIED_HTTPS_200`
- Backend-free and call-disabled: `VERIFIED`
- Microphone, WebSocket, LINE identity, MiniMax, LiveKit and database: `DISABLED`
- Browser policy: `microphone=() / connect-src 'none' / media-src 'none'`
- LINE Secret, access token, LIFF ID or provider credential added: `NO`
- Production changed: `NO`
- Ruff: `PASS`
- mypy strict: `PASS_87_FILES`
- pytest: `PASS_278`
- TypeScript strict: `PASS`
- Offline browser assertions: `PASS_22`
- Staging server tests: `PASS_3`
- Vite production build: `PASS`
- npm audit: `PASS_0_VULNERABILITIES`
- Stop condition: `NEEDS_HUMAN_LIFF_APP_CREATION`

## LIFF App Registration Verification and Public Configuration Contract

- Status: `COMPLETED / NEEDS_HUMAN_LIFF_IDENTITY_ACTIVATION_REVIEW`
- LIFF ID and LIFF URL classification: `PUBLIC_CONFIG`
- Public LIFF URL: `VERIFIED_HTTP_200`
- Public app name and LIFF ID: `VERIFIED_FROM_PUBLIC_HTML`
- Redirect behavior: `VERIFIED_CLIENT_SIDE_JAVASCRIPT_TO_EXPECTED_STAGING_ENDPOINT`
- HTTP redirect count: `0`; no 3xx redirect claim
- Fallback link: `VERIFIED_EXPECTED_STAGING_ENDPOINT`
- Staging endpoint and health: `VERIFIED_HTTP_200 / INTEGRATIONS_FALSE`
- Real-user authentication or personal-data request: `NO`
- LINE identity verification: `NOT_EXECUTED / NOT_VERIFIED`
- openid: `HUMAN_CONFIGURED_NOT_SCREENSHOT_VERIFIED`
- profile/chat scopes: `UNKNOWN_NOT_SCREENSHOT_VERIFIED`
- LIFF SDK, identity, profile, microphone, WebSocket, MiniMax, LiveKit, database, Mem0 and calls:
  `DISABLED`
- LIFF ID injected into Railway/runtime configuration: `NO`
- Channel Secret, Channel Access Token or credential added: `NO`
- Production changed or deployment triggered: `NO`
- Ruff: `PASS`
- mypy strict: `PASS` (88 source files)
- pytest: `PASS` (282 tests)
- TypeScript strict: `PASS`
- Offline browser assertions: `PASS` (22)
- Staging server tests: `PASS` (3)
- Vite production build: `PASS`
- JSON validation: `PASS` (3 files)
- Mission-file high-confidence secret findings: `0 / 8 FILES`
- Stop condition: `NEEDS_HUMAN_LIFF_IDENTITY_ACTIVATION_REVIEW`

## LIFF Identity Merge Review Repair

- Status: `LOCAL_VERIFIED / NEEDS_HUMAN_FINAL_MERGE_REVIEW`
- Branch: `codex/liff-staging-identity-activation`
- Merge performed: `NO`
- Deployment or production connection: `NO`
- Browser activation: separate `VITE_LIFF_IDENTITY_ENABLED` flag, default false
- Public LIFF ID alone loads SDK: `NO / TESTED`
- LIFF SDK surface: pluggable core + `isLoggedIn` + `getIDToken`
- Server activation: staging + calibration enabled + kill switch open + public bindings + allowlist
- Non-allowlisted subject: `DENIED / TESTED`
- Role source: existing `OwnerCalibrationPolicy`, not verifier input
- Provider binding: `LINE REQUIRED / TESTED`
- Channel audience binding: exact configured Channel ID required / tested
- Arbitrary transport exception cause: detached / traceback-redaction tested
- CSP connect allowlist: self + `https://api.line.me`; microphone/media remain denied
- Real LINE verification route/login: `NOT_IMPLEMENTED / NOT_EXECUTED`
- Ruff: `PASS`
- mypy strict: `PASS` (90 source files)
- pytest: `PASS` (305 tests)
- Frontend lint/typecheck: `PASS`
- Offline browser assertions: `PASS` (22 protocol + 41 LIFF identity)
- Staging server tests: `PASS` (3)
- Vite synthetic fail-closed build: `PASS`
- npm audit: `PASS / 0 vulnerabilities`
- High-confidence secret findings: `0`
- Tracy/legacy orchestrator findings: `0`
- Required stop: `NEEDS_HUMAN_FINAL_MERGE_REVIEW`

## LIFF Staging Identity Activation — Offline Implementation

- Status: `COMPLETED_OFFLINE_ONLY / NEEDS_HUMAN_LIFF_IDENTITY_ACTIVATION_REVIEW`
- Base: `codex/liff-registration-contract`
- LIFF settings: `HUMAN_SCREENSHOT_VERIFIED`
- Screenshot committed: `NO`
- LIFF ID, LIFF URL, Channel ID and issuer classification: `PUBLIC_CONFIG`
- Official LIFF SDK: `@line/liff 2.29.1 / LOCKED`
- Browser API surface: `init / isLoggedIn / getIDToken ONLY`
- Requested Console scope: `openid ONLY`
- Profile, email, friendship, chat, QR and share-target APIs: `ABSENT / FORBIDDEN`
- Missing/malformed public config: `FAIL_CLOSED / SDK NOT LOADED`
- Identity failure media gating: `CALL/MICROPHONE/WEBSOCKET/AI FALSE`
- Server verify contract: `LINE LOGIN V2.1 VERIFY ID TOKEN ENDPOINT`
- Trusted response validation: `iss / aud / exp / sub`
- Client-decoded token trusted: `NO`
- Phase 3B identity mapper reused: `YES`
- Tenant/persona mismatch: `REJECTED`
- Raw token/subject in repr, events or response: `0`
- Raw subject persisted: `NO`
- Real LINE login/network call: `0`
- Railway/runtime variables changed: `NO`
- Deployment, DB, Mem0, microphone, WebSocket, MiniMax, LiveKit and calls: `0`
- Ruff: `PASS`
- mypy strict: `PASS` (90 files)
- pytest: `PASS` (297 tests)
- Frontend identity lint: `PASS` (2 files)
- TypeScript strict: `PASS`
- Offline assertions: `PASS` (22 existing + 24 identity)
- Staging server tests: `PASS` (3)
- Vite build: `PASS`
- npm locked install: `PASS`; audit: `0 vulnerabilities`
- JSON validation: `PASS` (6 files)
- Mission-file high-confidence secret findings: `0 / 27 FILES`
- Forbidden runtime/client capability matches: `0 / 0`
- Stop condition: `NEEDS_HUMAN_LIFF_IDENTITY_ACTIVATION_REVIEW`
