import { createReadStream, existsSync } from "node:fs";
import { stat } from "node:fs/promises";
import { createServer } from "node:http";
import { extname, resolve, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const INTEGRATION_FLAGS = [
  "DATABASE_ENABLED",
  "EXTERNAL_PROVIDERS_ENABLED",
  "LIFF_IDENTITY_ENABLED",
  "LIVEKIT_ENABLED",
  "MICROPHONE_ENABLED",
  "MINIMAX_ENABLED",
  "WEBSOCKET_ENABLED",
];

const MIME_TYPES = new Map([
  [".css", "text/css; charset=utf-8"],
  [".html", "text/html; charset=utf-8"],
  [".js", "text/javascript; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".svg", "image/svg+xml"],
]);

export function assertSafeStagingEnvironment(env = process.env) {
  const railwayEnvironment = env.RAILWAY_ENVIRONMENT_NAME;
  if (railwayEnvironment && railwayEnvironment !== "staging") {
    throw new Error("LIFF shell refuses to run outside Railway staging");
  }
  for (const name of INTEGRATION_FLAGS) {
    if ((env[name] ?? "false").toLowerCase() !== "false") {
      throw new Error(`${name} must remain false for the LIFF staging shell`);
    }
  }
}

function safeAssetPath(distDirectory, requestPath) {
  const decoded = decodeURIComponent(requestPath.split("?")[0]);
  const relative = decoded === "/" ? "index.html" : decoded.replace(/^\/+/, "");
  const candidate = resolve(distDirectory, relative);
  const root = resolve(distDirectory);
  return candidate === root || candidate.startsWith(`${root}${sep}`) ? candidate : null;
}

function securityHeaders(contentType) {
  return {
    "cache-control": "no-store",
    "content-security-policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'none'; img-src 'self' data:; media-src 'none'; frame-ancestors https://access.line.me https://line.me https://liff.line.me",
    "content-type": contentType,
    "permissions-policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "referrer-policy": "no-referrer",
    "x-content-type-options": "nosniff",
  };
}

export function createStagingServer({ distDirectory, env = process.env } = {}) {
  assertSafeStagingEnvironment(env);
  const root = distDirectory ?? resolve(fileURLToPath(new URL("../dist", import.meta.url)));

  return createServer(async (request, response) => {
    if (request.url === "/healthz") {
      response.writeHead(200, securityHeaders("application/json; charset=utf-8"));
      response.end(JSON.stringify({ status: "ok", mode: "liff-staging-shell", integrations: false }));
      return;
    }

    let asset;
    try {
      asset = safeAssetPath(root, request.url ?? "/");
    } catch {
      asset = null;
    }
    if (asset === null) {
      response.writeHead(400, securityHeaders("text/plain; charset=utf-8"));
      response.end("Bad request");
      return;
    }
    try {
      if (!existsSync(asset) || !(await stat(asset)).isFile()) {
        asset = resolve(root, "index.html");
      }
      response.writeHead(200, securityHeaders(MIME_TYPES.get(extname(asset)) ?? "application/octet-stream"));
      createReadStream(asset).pipe(response);
    } catch {
      response.writeHead(404, securityHeaders("text/plain; charset=utf-8"));
      response.end("Not found");
    }
  });
}

const invokedDirectly = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (invokedDirectly) {
  const port = Number.parseInt(process.env.PORT ?? "3000", 10);
  const server = createStagingServer();
  server.listen(port, "0.0.0.0", () => {
    console.log(`LIFF staging shell listening on port ${port}`);
  });
}
