import assert from "node:assert/strict";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { assertSafeStagingEnvironment, createStagingServer } from "./staging-server.mjs";

test("refuses production", () => {
  assert.throws(
    () => assertSafeStagingEnvironment({ RAILWAY_ENVIRONMENT_NAME: "production" }),
    /outside Railway staging/,
  );
});

test("refuses every enabled integration", () => {
  for (const name of [
    "DATABASE_ENABLED", "EXTERNAL_PROVIDERS_ENABLED",
    "LIVEKIT_ENABLED", "MICROPHONE_ENABLED", "MINIMAX_ENABLED", "WEBSOCKET_ENABLED",
  ]) {
    assert.throws(() => assertSafeStagingEnvironment({ [name]: "true" }), new RegExp(name));
  }
});

test("serves shell and safe health response", async (context) => {
  const directory = await mkdtemp(join(tmpdir(), "plm-liff-shell-"));
  await writeFile(join(directory, "index.html"), "<!doctype html><title>staging</title>");
  const server = createStagingServer({ distDirectory: directory, env: {} });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  context.after(() => server.close());
  const address = server.address();
  assert.notEqual(address, null);
  assert.equal(typeof address, "object");
  if (typeof address !== "object" || address === null) return;

  const health = await fetch(`http://127.0.0.1:${address.port}/healthz`);
  assert.equal(health.status, 200);
  assert.deepEqual(await health.json(), {
    status: "ok", mode: "liff-staging-shell", integrations: false,
  });
  assert.match(health.headers.get("permissions-policy") ?? "", /microphone=\(\)/);
  assert.match(
    health.headers.get("content-security-policy") ?? "",
    /connect-src 'self' https:\/\/api\.line\.me/,
  );

  const index = await fetch(`http://127.0.0.1:${address.port}/`);
  assert.equal(index.status, 200);
  assert.match(await index.text(), /staging/);
});
