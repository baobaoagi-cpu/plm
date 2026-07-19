import { DialTone } from "./DialTone";
import { MicPermission } from "./MicPermission";
import { Waveform } from "./Waveform";

export const CALIBRATION_NOTICE =
  "目前為本人校準測試版本。內容尚未代表謝文憲老師正式立場。";

interface CalibrationCallShellProps {
  microphoneGranted: boolean;
  callEnabled?: boolean;
  connecting?: boolean;
  onAllowMicrophone: () => void;
  onClose: () => void;
  onStartCall: () => void;
}

export function CalibrationCallShell({
  microphoneGranted,
  callEnabled = false,
  connecting = false,
  onAllowMicrophone,
  onClose,
  onStartCall,
}: CalibrationCallShellProps) {
  if (!microphoneGranted) {
    return <MicPermission onAllow={onAllowMicrophone} onDeny={onClose} />;
  }

  return (
    <main
      style={{
        alignItems: "center",
        background: "#101412",
        color: "#f6f8f7",
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        padding: 24,
      }}
    >
      <p style={{ background: "#25332c", borderRadius: 12, padding: 12 }}>{CALIBRATION_NOTICE}</p>
      <h1>謝文憲 AI 分身｜本人校準版</h1>
      <Waveform active={connecting} />
      <DialTone playing={connecting} />
      <button disabled={!callEnabled || connecting} onClick={onStartCall}>
        {callEnabled ? "開始校準通話" : "即時通話尚未接線"}
      </button>
      <button onClick={onClose}>關閉</button>
    </main>
  );
}
