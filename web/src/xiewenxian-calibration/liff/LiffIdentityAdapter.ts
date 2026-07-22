export const OPENID_SCOPE = "openid" as const;

const LIFF_ID_PATTERN = /^[0-9]{8,20}-[A-Za-z0-9_-]{4,64}$/;

export interface LiffPublicConfig {
  readonly liffId: string;
  readonly requestedScopes: readonly [typeof OPENID_SCOPE];
}

export interface MinimalLiffSdk {
  init(config: { liffId: string; withLoginOnExternalBrowser: false }): Promise<void>;
  isLoggedIn(): boolean;
  getIDToken(): string | null;
}

export type IdentityStatus =
  | "configuration_missing"
  | "configuration_invalid"
  | "initializing"
  | "not_authenticated"
  | "verified"
  | "failed";

export interface IdentityCapabilities {
  readonly call: false;
  readonly microphone: false;
  readonly websocket: false;
  readonly ai: false;
}

export interface IdentityActivationResult {
  readonly status: IdentityStatus;
  readonly code: string;
  readonly capabilities: IdentityCapabilities;
}

export interface TokenVerificationResult {
  readonly verified: boolean;
  readonly code: string;
}

export type LiffSdkLoader = () => Promise<MinimalLiffSdk>;
export type VerifyIdToken = (idToken: string) => Promise<TokenVerificationResult>;

const DISABLED_CAPABILITIES: IdentityCapabilities = Object.freeze({
  call: false,
  microphone: false,
  websocket: false,
  ai: false,
});

function result(status: IdentityStatus, code: string): IdentityActivationResult {
  return { status, code, capabilities: DISABLED_CAPABILITIES };
}

export function loadLiffPublicConfig(rawLiffId: string | undefined): LiffPublicConfig | null {
  if (rawLiffId === undefined || rawLiffId.trim() === "") {
    return null;
  }
  const liffId = rawLiffId.trim();
  if (!LIFF_ID_PATTERN.test(liffId)) {
    throw new Error("invalid_public_liff_config");
  }
  return { liffId, requestedScopes: [OPENID_SCOPE] };
}

export async function loadOfficialLiffSdk(): Promise<MinimalLiffSdk> {
  const module = await import("@line/liff");
  return module.default;
}

export async function activateLiffIdentity(
  rawLiffId: string | undefined,
  loadSdk: LiffSdkLoader,
  verifyIdToken: VerifyIdToken,
): Promise<IdentityActivationResult> {
  let config: LiffPublicConfig | null;
  try {
    config = loadLiffPublicConfig(rawLiffId);
  } catch {
    return result("configuration_invalid", "invalid_public_liff_config");
  }
  if (config === null) {
    return result("configuration_missing", "public_liff_config_missing");
  }

  try {
    const sdk = await loadSdk();
    await sdk.init({ liffId: config.liffId, withLoginOnExternalBrowser: false });
    if (!sdk.isLoggedIn()) {
      return result("not_authenticated", "line_session_unavailable");
    }
    const idToken = sdk.getIDToken();
    if (idToken === null || idToken.length < 16 || idToken.split(".").length !== 3) {
      return result("failed", "id_token_unavailable");
    }
    const verification = await verifyIdToken(idToken);
    return verification.verified
      ? result("verified", "verified")
      : result("failed", verification.code);
  } catch {
    return result("failed", "identity_activation_failed");
  }
}
