# LIFF Staging Identity Boundary

Status: `IMPLEMENTED_OFFLINE_ONLY / NOT_DEPLOYED`

## Reused identity path

This Mission extends the existing Phase 3B path instead of creating another identity system:

1. The browser initializes the official LIFF SDK only when `VITE_LIFF_ID` exists and is valid.
2. The adapter uses only `liff.getIDToken()`; it does not decode claims or expose profile methods.
3. A future server route passes the opaque token and expected public Channel ID through
   `LineIdTokenVerifyTransport` to LINE's official verify-ID-token endpoint.
4. `LineIdTokenVerifier` checks the trusted response's issuer, audience, expiry and subject.
5. `LineIdentityBoundary` immediately hands the verified assertion to the existing
   `map_verified_identity()` function.
6. The returned response contains the tenant-bound effective ID summary only. Raw token and raw
   LINE subject are neither returned nor persisted.

No HTTP route or real transport is connected in this Mission. All tests use deterministic fakes.

## Browser boundary

- Required scope: `openid` only, verified by human screenshot in the LIFF Console.
- `withLoginOnExternalBrowser` is false; the adapter does not call `liff.login()`.
- No `getDecodedIDToken`, `getProfile`, `getFriendship`, `sendMessages`, `scanCode`,
  `shareTargetPicker`, email, display-name or avatar access exists in the adapter.
- Missing or malformed build config prevents SDK loading.
- Identity failure leaves call, microphone, WebSocket and AI capabilities false.
- The deployed Railway service remains unchanged and still has no public LIFF build variable.

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
subject return safe codes without provider bodies or identity values.

Official references:

- https://developers.line.biz/en/reference/line-login/#verify-id-token
- https://developers.line.biz/en/reference/liff/#get-id-token
- https://developers.line.biz/en/docs/liff/developing-liff-apps/#integrating-liff-sdk

## Human application checklist for a future deployment gate

- Confirm the public Channel ID for `憲哥 Digital Twin`.
- Apply the public LIFF ID to `VITE_LIFF_ID` and the server LIFF slot.
- Apply the same public Channel ID as the expected verification audience.
- Keep issuer fixed to the official LINE issuer.
- Enable only `LIFF_IDENTITY_ENABLED`; leave broad LINE integration and every voice/data flag off.
- Review CSP/network allowlists before deployment; do not weaken them in this offline Mission.
- Verify with consented staging test identities under a separate real-login authorization.

Required stop: `NEEDS_HUMAN_LIFF_IDENTITY_ACTIVATION_REVIEW`.
