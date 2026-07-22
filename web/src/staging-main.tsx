import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { CalibrationCallShell } from "./xiewenxian-calibration/CalibrationCallShell";
import "./staging.css";

function StagingShell() {
  return (
    <div className="staging-frame">
      <aside className="staging-banner" role="status">
        STAGING · 僅供本人校準介面驗收 · 所有連線功能均已關閉
      </aside>
      <CalibrationCallShell
        callEnabled={false}
        connecting={false}
        microphoneGranted={true}
        onAllowMicrophone={() => undefined}
        onClose={() => window.history.back()}
        onStartCall={() => undefined}
      />
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
