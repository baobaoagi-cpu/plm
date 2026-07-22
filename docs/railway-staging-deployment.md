# Railway Staging Deployment Readiness

## Scope

This deployment is a health-only staging shell. It proves the delivery path from GitHub to
Railway and does not start the formal duplex runtime.

- Railway environment: `staging` only
- Public routes: `GET /` and `GET /healthz`
- External providers, LINE, LiveKit and databases: disabled
- Owner Calibration sandbox mode: required
- Kill switch: required
- Production persona, real users and real data: absent

`railway.toml` deliberately places the start command under `environments.staging`. The repository
does not provide a production start command.

## Expected health response

`GET /healthz` returns HTTP 200 with a small JSON document identifying this process as the
`plm-staging-deployment-shell`. It reports that the process is not production-ready and that
external integrations are disabled. The response contains no credentials, provider identifiers,
user data or runtime configuration values.

## Fail-closed startup rules

The process refuses to start if any of the following is true:

- `APP_ENV` is not `staging`;
- Railway reports an environment other than `staging`;
- provider, LINE, database, admin HTTP or LiveKit integration is enabled;
- Owner Calibration sandbox mode is disabled;
- the kill switch is disabled; or
- `PORT` is invalid.

## Deployment flow

1. Push the approved branch and open a Draft PR.
2. Require GitHub Actions to pass.
3. Configure the Railway persistent `staging` environment to track the approved Git branch.
4. Let Railway build from GitHub using the repository's config-as-code file.
5. Confirm Railway's deployment health check receives HTTP 200 from `/healthz`.
6. Confirm the generated public staging domain returns the same response.

Do not copy variables from production. This shell requires no third-party secret.

## 2026-07-22 execution evidence

- Git branch: `codex/railway-staging-readiness`
- Git commit: `ebdfcbb7efd97759abc1bd31ffe03aa20d43b4e8`
- Draft PR: `https://github.com/baobaoagi-cpu/plm/pull/6`
- GitHub Actions: two quality runs passed
- Railway environment: `staging` (`ba28d01d-df40-4734-9cd3-ac1dbbe3a8ee`)
- Railway service: `plm-staging-readiness` (`6a3d2127-28cb-43f6-a950-58f5c1de2617`)
- Railway deployment: `cd298968-004a-45e6-a09a-fb5aae645950` / `SUCCESS`
- Public health URL: `https://plm-staging-readiness-staging.up.railway.app/healthz`
- Public health response: HTTP 200, staging, production not ready, external integrations disabled
- Production deployment changed: no
- GitHub source autodeploy: blocked; Railway returned `Unauthorized` while attaching the repo

The successful Railway deployment used `railway up` from the exact committed branch. This verifies
the build, start, healthcheck and public networking path, but it does not verify GitHub autodeploy.
The service must be granted access to `baobaoagi-cpu/plm` and connected to the branch before that
claim can be upgraded.

## Stop condition

After GitHub autodeploy is verified, the milestone stops at
`NEEDS_HUMAN_STAGING_DEPLOYMENT_REVIEW`. Until then it remains
`NEEDS_HUMAN_RAILWAY_GITHUB_SOURCE_AUTH`. It does not authorize production deployment, LINE OA
delivery, provider calls, database connections or the formal voice pipeline.
