import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const files = [
  "src/staging-main.tsx",
  "src/xiewenxian-calibration/liff/LiffIdentityAdapter.ts",
];
const forbidden = [
  "getDecodedIDToken",
  "getProfile",
  "getFriendship",
  "sendMessages",
  "scanCode",
  "shareTargetPicker",
  "getUserMedia",
  "new WebSocket",
  "console.log",
];

for (const file of files) {
  const source = readFileSync(resolve(file), "utf8");
  for (const fragment of forbidden) {
    if (source.includes(fragment)) {
      throw new Error(`${file} contains forbidden identity capability: ${fragment}`);
    }
  }
}

console.log(`LIFF_IDENTITY_LINT_PASS files=${files.length}`);
