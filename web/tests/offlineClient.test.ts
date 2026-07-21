import { OfflineClientStateMachine } from "../src/xiewenxian-calibration/offline/ClientStateMachine.js";
import {
  OfflineDuplexAudioLab,
  observeEchoCancellation,
} from "../src/xiewenxian-calibration/offline/DuplexAudioLab.js";
import {
  PCM16_FRAME_BYTES,
  Pcm16Framer,
} from "../src/xiewenxian-calibration/offline/Pcm16Framer.js";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function expectThrow(run: () => void, message: string): void {
  let threw = false;
  try {
    run();
  } catch {
    threw = true;
  }
  assert(threw, message);
}

const framer = new Pcm16Framer(48_000);
const samples = new Float32Array(960).fill(0.5);
const frames = framer.push(samples);
assert(frames.length === 1, "48 kHz input must produce one 20 ms frame");
assert(frames[0]?.byteLength === PCM16_FRAME_BYTES, "PCM frame must contain 640 bytes");
assert(frames[0]?.[0] === 0 && frames[0]?.[1] === 64, "PCM must be signed 16-bit LE");

const lab = new OfflineDuplexAudioLab({ maxInputFrames: 20, maxOutputBytes: 100 });
lab.startGeneration("generation-1");
assert(lab.queueAssistantAudio("generation-1", 1, new Uint8Array([1, 2, 3])), "active audio accepted");
for (let index = 0; index < 10; index += 1) {
  lab.captureMicrophone(new Uint8Array(PCM16_FRAME_BYTES));
}
assert(lab.snapshot().capturedFrames === 10, "microphone must continue while playback is queued");
assert(lab.interrupt("generation-1") === 1, "interrupt must hard-clear playback");
assert(!lab.queueAssistantAudio("generation-1", 2, new Uint8Array([4])), "late audio must be stale");
lab.startGeneration("generation-2");
assert(lab.queueAssistantAudio("generation-2", 1, new Uint8Array([5])), "new generation accepted");
assert(lab.playNext()?.[0] === 5, "new generation audio must play");
lab.hangup();
lab.hangup();
assert(lab.snapshot().ended, "hangup must be idempotent");
assert(lab.snapshot().queuedInputFrames === 0, "hangup must clear microphone queue");
expectThrow(
  () => lab.captureMicrophone(new Uint8Array(PCM16_FRAME_BYTES)),
  "ended lab must reject microphone data",
);

const state = new OfflineClientStateMachine();
for (const event of [
  "request_permission",
  "permission_granted",
  "transport_ready",
  "duplex_started",
  "interrupt",
  "playback_cleared",
  "transport_lost",
  "retry",
  "transport_ready",
  "hangup",
] as const) {
  state.dispatch(event);
}
assert(state.state === "ended", "state machine must terminate after hangup");
assert(state.stateRevision === 10, "every accepted transition must increment revision");
expectThrow(() => state.dispatch("retry"), "ended state must be terminal");

assert(observeEchoCancellation({ echoCancellation: true }) === "enabled", "AEC enabled observation");
assert(observeEchoCancellation({ echoCancellation: false }) === "disabled", "AEC disabled observation");
assert(observeEchoCancellation(undefined) === "unreported", "AEC absence must remain unknown");

console.log("OFFLINE_CLIENT_TESTS_PASS assertions=19");
