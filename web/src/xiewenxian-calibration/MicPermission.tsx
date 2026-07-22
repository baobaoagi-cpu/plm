interface MicPermissionProps {
  onAllow: () => void;
  onDeny: () => void;
}

const panelStyle = {
  alignItems: "center",
  background: "#101412",
  color: "#f6f8f7",
  display: "flex",
  flexDirection: "column",
  inset: 0,
  justifyContent: "center",
  padding: 24,
  position: "fixed",
} as const;

const buttonStyle = {
  border: 0,
  borderRadius: 999,
  cursor: "pointer",
  fontSize: 16,
  marginTop: 12,
  padding: "12px 28px",
} as const;

export function MicPermission({ onAllow, onDeny }: MicPermissionProps) {
  return (
    <section aria-labelledby="microphone-title" style={panelStyle}>
      <div aria-hidden="true" style={{ fontSize: 42 }}>
        ◉
      </div>
      <h1 id="microphone-title">允許使用麥克風嗎？</h1>
      <p>只有按下「允許」後，瀏覽器才會請求麥克風權限。</p>
      <button onClick={onAllow} style={{ ...buttonStyle, background: "#24a767", color: "white" }}>
        允許
      </button>
      <button onClick={onDeny} style={{ ...buttonStyle, background: "transparent", color: "#bec8c2" }}>
        關閉
      </button>
    </section>
  );
}
