# Current Milestone Plan

## Milestone

`Railway Staging Deployment Readiness`

## Goal

Prove the GitHub-to-Railway staging delivery path with a health-only, fail-closed service before any
formal runtime or external integration is authorized.

## Delivered and published

- Railway config-as-code scoped only to the `staging` environment.
- Dependency-free HTTP shell on Railway's assigned port.
- `GET /healthz` with no secrets, identity, provider or user data.
- Hard refusal outside staging or when an external integration, disabled sandbox or disabled kill
  switch is detected.
- Branch `codex/railway-staging-readiness`, commit `ebdfcbb7efd97759abc1bd31ffe03aa20d43b4e8`
  and Draft PR #6.
- Two passing GitHub Actions quality runs.
- Empty Railway `staging` environment created without copying production.
- Railway deployment `cd298968-004a-45e6-a09a-fb5aae645950` succeeded from the exact committed
  branch via CLI upload.
- Public `/healthz` returned HTTP 200 and confirmed external integrations disabled.

## Pending human action

- Grant the Railway GitHub integration access to `baobaoagi-cpu/plm`.
- Connect service `plm-staging-readiness` to branch `codex/railway-staging-readiness`.
- Return to Codex so a GitHub-triggered deployment can be observed and verified.

## Explicitly not delivered

- GitHub autodeploy proof; the repository attachment returned `Unauthorized`.
- Production deployment or production start command.
- LINE, MiniMax, LiveKit, database, Mem0 or real-user integration.
- Formal MiniMaxTTSService, Pipecat Pipeline or voice runtime.

## Required stop

`NEEDS_HUMAN_RAILWAY_GITHUB_SOURCE_AUTH`
