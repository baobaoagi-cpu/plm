# LIFF Staging Identity Threat Model

Status: `OFFLINE_VERIFIED / REAL_LOGIN_NOT_EXECUTED`

| Threat | Fail-closed control | Evidence |
|---|---|---|
| Client forges decoded claims | Server accepts opaque ID token only; decoded client payload is never trusted | verifier interface and tests |
| Token targets another channel | Trusted response `aud` must equal configured public Channel ID | wrong-audience test |
| Token comes from another issuer | `iss` must equal `https://access.line.me` | wrong-issuer test |
| Expired token replay | Integer `exp` must be later than server time | expired-token test |
| Missing or malformed identity | Bounded JWT shape and non-empty bounded subject required | missing/malformed tests |
| Provider stalls or fails | Bounded timeout and safe upstream error mapping | timeout/error tests |
| Cross-tenant/persona use | Settings bind to existing Xie Wenxian namespace and persona | mismatch tests |
| Token or subject leaks | Secret fields use redacted repr; events/responses contain safe codes and hashes only | redaction tests |
| Profile or email overcollection | `name`, `picture` and `email` claims are rejected; forbidden client APIs are linted | claim/lint tests |
| Identity failure unlocks media | Frontend capabilities remain false for call, microphone, WebSocket and AI | offline frontend tests |
| Missing build config loads SDK | SDK loader is not invoked without valid public LIFF config | offline frontend tests |

## Residual unknowns

- Real LIFF browser initialization, ID-token delivery and user-consent UX are not executed.
- The public LINE Login Channel ID has not been supplied to runtime configuration.
- No backend HTTP route or LINE network transport is connected.
- Railway CSP/network changes required by a future deployment have not been evaluated or applied.
- No DB, Mem0, LINE subject persistence, profile, webhook or voice runtime exists.

These unknowns require a separately authorized real-login staging gate. They cannot be inferred from
offline fixtures.
