# LIFF Staging Identity Boundary

Status: `IMPLEMENTED_OFFLINE_ONLY / NOT_DEPLOYED`

## Reused identity path

This Mission extends the existing Phase 3B path instead of creating another identity system:

1. The browser initializes the official LIFF SDK only when
   `VITE_LIFF_IDENTITY_ENABLED=true` and `VITE_LIFF_ID` exists and is valid.
2. The adapter installs only the pluggable LIFF core, `isLoggedIn` and `getIDToken` modules; it
   does not decode claims or expose profile methods.
3. A future server route passes the opaque token and expected public Channel ID through
   `LineIdTokenVerifyTransport` to LINE's official verify-ID-token endpoint.
4. `LineIdTokenVerifier` checks the trusted response's issuer, audience, expiry and subject.
5. `LineIdentityBoundary` requires a LINE assertion bound to the same Channel audience, then
   applies the existing fail-closed calibration allowlist, kill switch and role policy.
6. Only an authorized assertion is handed to the existing `map_verified_identity()` function.
7. The returned response contains the tenant-bound effective ID summary only. Raw token and raw
   LINE subject are neither returned nor persisted.

No HTTP route or real transport is connected in this Mission. All tests use deterministic fakes.

## Browser boundary

- Required scope: `openid` only, verified by human screenshot in the LIFF Console.
- `withLoginOnExternalBrowser` is false; the adapter does not call `liff.login()`.
- No `getDecodedIDToken`, `getProfile`, `getFriendship`, `sendMessages`, `scanCode`,
  `shareTargetPicker`, email, display-name or avatar access exists in the adapter.
- A missing/false browser activation flag or missing/malformed build config prevents SDK loading.
- Identity failure leaves call, microphone, WebSocket and AI capabilities false.
- The public LIFF ID was staged in Railway without a deployment. The browser activation flag
  remains absent/false, so a later rebuild still fails closed and does not initialize LIFF.

## Server boundary

The official request contract is a form POST to
`https://api.line.me/oauth2/v2.1/verify` with the opaque `id_token` and expected public `client_id`
(LINE Login Channel ID). The transport is replaceable and injected; the implementation never
trusts `liff.getDecodedIDToken()` or any client-supplied decoded claims.

The trusted response must contain:

- `iss` exactly `https://access.line.me`;
- `aud` exactly the configured Channel ID;
- an integer `exp` later than the server's current time; and
- a non-empty bounded `sub`.

Responses containing `name`, `picture` or `email` fail closed because this registration is
openid-only. Timeout, transport error, malformed token, wrong issuer/audience, expiry and missing
subject return safe codes without provider bodies or identity values. Arbitrary transport
exceptions are deliberately detached from the safe public exception so traceback logging cannot
retain a request body containing the token.

The offline boundary also rejects assertions from another provider or another Channel, and denies
every LINE subject not present in `XIEWENXIAN_CALIBRATION_LINE_ALLOWLIST_JSON`. Allowlisted roles
are resolved by `OwnerCalibrationPolicy`; a verifier cannot self-assign an elevated role.

Official references:

- https://developers.line.biz/en/reference/line-login/#verify-id-token
- https://developers.line.biz/en/reference/liff/#get-id-token
- https://developers.line.biz/en/docs/liff/developing-liff-apps/#integrating-liff-sdk

## Human application checklist for a future deployment gate

- Confirm the public Channel ID for `憲哥 Digital Twin`.
- Apply the public LIFF ID to `VITE_LIFF_ID` and the server LIFF slot.
- Enable `VITE_LIFF_IDENTITY_ENABLED` only in the separately reviewed browser build.
- Apply the same public Channel ID as the expected verification audience.
- Keep issuer fixed to the official LINE issuer.
- Enable server `LIFF_IDENTITY_ENABLED` only with calibration enabled, the kill switch deliberately
  opened and an environment-only allowlist; leave broad LINE integration and every voice/data flag
  off.
- The shell CSP permits only self and `https://api.line.me` connections; any future verification
  route requires a separate route/CORS/rate-limit review before deployment.
- Verify with consented staging test identities under a separate real-login authorization.

Required stop: `NEEDS_HUMAN_FINAL_MERGE_REVIEW`.
