export type OfflineCallState =
  | "idle"
  | "permission_required"
  | "connecting"
  | "ready"
  | "duplex_active"
  | "interrupting"
  | "reconnecting"
  | "ended"
  | "failed";

export type OfflineCallEvent =
  | "request_permission"
  | "permission_granted"
  | "transport_ready"
  | "duplex_started"
  | "interrupt"
  | "playback_cleared"
  | "transport_lost"
  | "retry"
  | "hangup"
  | "fatal_error";

const transitions: Readonly<
  Partial<Record<OfflineCallState, Partial<Record<OfflineCallEvent, OfflineCallState>>>>
> = {
  idle: { request_permission: "permission_required", hangup: "ended" },
  permission_required: { permission_granted: "connecting", hangup: "ended" },
  connecting: { transport_ready: "ready", transport_lost: "reconnecting", hangup: "ended" },
  ready: { duplex_started: "duplex_active", transport_lost: "reconnecting", hangup: "ended" },
  duplex_active: {
    interrupt: "interrupting",
    transport_lost: "reconnecting",
    hangup: "ended",
  },
  interrupting: {
    playback_cleared: "ready",
    transport_lost: "reconnecting",
    hangup: "ended",
  },
  reconnecting: { retry: "connecting", hangup: "ended" },
  failed: { retry: "connecting", hangup: "ended" },
};

export class OfflineClientStateMachine {
  private current: OfflineCallState = "idle";
  private revision = 0;

  get state(): OfflineCallState {
    return this.current;
  }

  get stateRevision(): number {
    return this.revision;
  }

  dispatch(event: OfflineCallEvent): OfflineCallState {
    if (event === "fatal_error" && this.current !== "ended") {
      this.current = "failed";
      this.revision += 1;
      return this.current;
    }
    const next = transitions[this.current]?.[event];
    if (!next) throw new Error("invalid offline call state transition");
    this.current = next;
    this.revision += 1;
    return next;
  }
}
