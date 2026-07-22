# Iteration 017 - Railway Staging Deployment Readiness

## Single goal

Create a staging-only GitHub-to-Railway delivery shell with a public health check, without touching
production or enabling any formal runtime or external integration.

## Implementation and local proof

- Added staging-scoped Railway config-as-code.
- Added a dependency-free HTTP shell bound to `0.0.0.0:$PORT`.
- Startup fails closed outside staging and if any external integration is enabled.
- Ruff passed; mypy strict passed for 87 files; all 278 pytest tests passed.
- TypeScript strict and 22 offline browser assertions passed.
- Local `/healthz` returned HTTP 200.
- High-confidence secret and forbidden-runtime scans returned zero findings.

## GitHub proof

- Branch: `codex/railway-staging-readiness`
- Commit: `ebdfcbb7efd97759abc1bd31ffe03aa20d43b4e8`
- Draft PR: `https://github.com/baobaoagi-cpu/plm/pull/6`
- Push and pull-request quality runs: pass.

## Railway proof

- Created a new empty `staging` environment; production was not duplicated.
- Created service `plm-staging-readiness` with only non-secret safety flags.
- CLI upload from the exact committed branch deployed successfully.
- Railway healthcheck and the public `/healthz` endpoint returned HTTP 200.
- Response confirmed staging, production not ready and external integrations disabled.
- No LINE, MiniMax, LiveKit, database, Mem0 or real-user connection occurred.

## Blocker

Railway returned `Unauthorized` when attaching `baobaoagi-cpu/plm` as the GitHub source. Account
authentication remained valid, so GitHub integration repository access requires human repair.
GitHub autodeploy is not claimed as verified.

Decision: `NEEDS_HUMAN_RAILWAY_GITHUB_SOURCE_AUTH`.
