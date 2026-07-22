# LIFF Staging Frontend Bootstrap

## Delivered boundary

The deployed site is a backend-free, call-disabled rendering of the existing owner-calibration
shell. It does not load the LIFF SDK, request microphone permission, open a WebSocket, call a
provider, or connect to a database. It contains no LINE secret, access token, LIFF ID, Voice ID,
or other credential.

## Public staging endpoint

- Endpoint: `https://plm-liff-staging-shell-staging.up.railway.app/`
- Health: `https://plm-liff-staging-shell-staging.up.railway.app/healthz`
- Railway environment: `staging`
- Railway service: `plm-liff-staging-shell`
- Deployment: `d4c0d20e-d5b4-4136-9239-2d3b4a86c551`

Both endpoints returned HTTPS 200. The health response reports `integrations: false`.

## Enforced controls

- Startup refuses a named Railway environment other than `staging`.
- Startup refuses any enabled database, provider, LINE identity, LiveKit, microphone, MiniMax, or
  WebSocket flag.
- `Permissions-Policy` disables camera, microphone, geolocation, and payment.
- CSP uses `connect-src 'none'` and `media-src 'none'`.
- The call control stays disabled and is labelled `即時通話尚未接線`.
- The page is marked `noindex, nofollow` and visibly labelled staging.

## Next human action

In the LINE Login channel, create one LIFF app using the public endpoint above. This milestone does
not authorize adding the generated LIFF ID to code, enabling LINE identity, or connecting any
backend. Stop at `NEEDS_HUMAN_LIFF_APP_CREATION`.
