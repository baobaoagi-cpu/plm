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

## Stop condition

Successful deployment stops at `NEEDS_HUMAN_STAGING_DEPLOYMENT_REVIEW`. It does not authorize
production deployment, LINE OA delivery, provider calls, database connections or the formal voice
pipeline.
