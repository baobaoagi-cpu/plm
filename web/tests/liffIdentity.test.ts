import assert from "node:assert/strict";

import {
  activateLiffIdentity,
  loadLiffPublicConfig,
  type MinimalLiffSdk,
} from "../src/xiewenxian-calibration/liff/LiffIdentityAdapter.js";

const LIFF_ID = "2010776532-YooRYUEg";
const SYNTHETIC_TOKEN = "synthetic-header.synthetic-payload.synthetic-signature";

async function main() {
  assert.deepEqual(loadLiffPublicConfig(LIFF_ID), {
    liffId: LIFF_ID,
    requestedScopes: ["openid"],
  });
  assert.equal(loadLiffPublicConfig(undefined), null);

  let sdkLoaded = false;
  let verifierCalled = false;
  const disabled = await activateLiffIdentity(
    "false",
    LIFF_ID,
    async () => {
      sdkLoaded = true;
      throw new Error("must not load");
    },
    async () => {
      verifierCalled = true;
      return { verified: true, code: "verified" };
    },
  );
  assert.equal(disabled.status, "disabled");
  assert.equal(sdkLoaded, false);
  assert.equal(verifierCalled, false);

  const missing = await activateLiffIdentity(
    "true",
    undefined,
    async () => {
      sdkLoaded = true;
      throw new Error("must not load");
    },
    async () => {
      verifierCalled = true;
      return { verified: true, code: "verified" };
    },
  );
  assert.equal(missing.status, "configuration_missing");
  assert.equal(sdkLoaded, false);
  assert.equal(verifierCalled, false);

  const invalid = await activateLiffIdentity("true", "invalid", async () => {
    throw new Error("must not load");
  }, async () => ({ verified: true, code: "verified" }));
  assert.equal(invalid.status, "configuration_invalid");

  let initializedWith: unknown;
  const sdk: MinimalLiffSdk = {
    async init(config) {
      initializedWith = config;
    },
    isLoggedIn: () => true,
    getIDToken: () => SYNTHETIC_TOKEN,
  };
  let receivedToken = "";
  const verified = await activateLiffIdentity(
    "true",
    LIFF_ID,
    async () => sdk,
    async (token) => {
      receivedToken = token;
      return { verified: true, code: "verified" };
    },
  );
  assert.deepEqual(initializedWith, {
    liffId: LIFF_ID,
    withLoginOnExternalBrowser: false,
  });
  assert.equal(receivedToken, SYNTHETIC_TOKEN);
  assert.equal(verified.status, "verified");
  assert.deepEqual(verified.capabilities, {
    call: false,
    microphone: false,
    websocket: false,
    ai: false,
  });
  assert.equal("idToken" in verified, false);

  const loggedOut = await activateLiffIdentity(
    "true",
    LIFF_ID,
    async () => ({ ...sdk, isLoggedIn: () => false }),
    async () => {
      throw new Error("must not verify");
    },
  );
  assert.equal(loggedOut.status, "not_authenticated");

  const rejected = await activateLiffIdentity(
    "true",
    LIFF_ID,
    async () => sdk,
    async () => ({ verified: false, code: "wrong_audience" }),
  );
  assert.equal(rejected.status, "failed");
  assert.equal(rejected.code, "wrong_audience");
  assert.equal(Object.values(rejected.capabilities).some(Boolean), false);

  for (const malformedToken of [null, "short", "a.b", "a.b.c.d"]) {
    let malformedVerifierCalled = false;
    const malformed = await activateLiffIdentity(
      "TRUE",
      LIFF_ID,
      async () => ({ ...sdk, getIDToken: () => malformedToken }),
      async () => {
        malformedVerifierCalled = true;
        return { verified: true, code: "verified" };
      },
    );
    assert.equal(malformed.status, "failed");
    assert.equal(malformed.code, "id_token_unavailable");
    assert.equal(malformedVerifierCalled, false);
  }

  const verifierFailure = await activateLiffIdentity(
    "true",
    LIFF_ID,
    async () => sdk,
    async () => {
      throw new Error(SYNTHETIC_TOKEN);
    },
  );
  assert.equal(verifierFailure.code, "identity_activation_failed");
  assert.equal(JSON.stringify(verifierFailure).includes(SYNTHETIC_TOKEN), false);

  const sdkFailure = await activateLiffIdentity(
    "true",
    LIFF_ID,
    async () => {
      throw new Error(SYNTHETIC_TOKEN);
    },
    async () => ({ verified: true, code: "verified" }),
  );
  assert.equal(sdkFailure.code, "identity_activation_failed");
  assert.equal(JSON.stringify(sdkFailure).includes(SYNTHETIC_TOKEN), false);

  console.log("LIFF_IDENTITY_TESTS_PASS assertions=41");
}

void main();
