import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

import { CalibrationCallShell } from "./xiewenxian-calibration/CalibrationCallShell";
import {
  activateLiffIdentity,
  loadOfficialLiffSdk,
  type IdentityStatus,
} from "./xiewenxian-calibration/liff/LiffIdentityAdapter";
import "./staging.css";

function StagingShell() {
  const [identityStatus, setIdentityStatus] = useState<IdentityStatus>("initializing");

  useEffect(() => {
    let active = true;
    void activateLiffIdentity(
      import.meta.env.VITE_LIFF_IDENTITY_ENABLED,
      import.meta.env.VITE_LIFF_ID,
      loadOfficialLiffSdk,
      async () => ({
        verified: false,
        code: "server_verification_boundary_unavailable",
      }),
    ).then((result) => {
      if (active) {
        setIdentityStatus(result.status);
      }
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="staging-frame">
      <aside className="staging-banner" role="status">
        STAGING · 僅供本人校準介面驗收 · 所有連線功能均已關閉
      </aside>
      <CalibrationCallShell
        callEnabled={false}
        connecting={false}
        microphoneGranted={false}
        onAllowMicrophone={() => undefined}
        onClose={() => window.history.back()}
        onStartCall={() => undefined}
      />
      <p className="staging-identity" role="status">
        LINE 身份狀態：{identityStatus}。即時通話仍停用。
      </p>
      <footer className="staging-safety">
        麥克風、LINE 身份、WebSocket、MiniMax、LiveKit 與資料庫皆未連接。
      </footer>
    </div>
  );
}

const rootElement = document.getElementById("root");
if (rootElement === null) {
  throw new Error("Missing root element");
}

createRoot(rootElement).render(
  <StrictMode>
    <StagingShell />
  </StrictMode>,
);
