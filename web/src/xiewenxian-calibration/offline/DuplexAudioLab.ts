import { PCM16_FRAME_BYTES } from "./Pcm16Framer.js";

interface OutputFrame {
  readonly generationId: string;
  readonly sequence: number;
  readonly payload: Uint8Array;
}

export interface DuplexLabSnapshot {
  readonly activeGenerationId: string | null;
  readonly capturedFrames: number;
  readonly queuedInputFrames: number;
  readonly queuedOutputFrames: number;
  readonly queuedOutputBytes: number;
  readonly clearedOutputFrames: number;
  readonly staleOutputFrames: number;
  readonly playedOutputFrames: number;
  readonly ended: boolean;
}

export type EchoCancellationObservation = "enabled" | "disabled" | "unreported";

export function observeEchoCancellation(
  settings: Pick<MediaTrackSettings, "echoCancellation"> | undefined,
): EchoCancellationObservation {
  if (settings?.echoCancellation === true) return "enabled";
  if (settings?.echoCancellation === false) return "disabled";
  return "unreported";
}

export class OfflineDuplexAudioLab {
  private readonly maxInputFrames: number;
  private readonly maxOutputBytes: number;
  private readonly inputFrames: Uint8Array[] = [];
  private readonly outputFrames: OutputFrame[] = [];
  private activeGenerationId: string | null = null;
  private lastQueuedOutputSequence = 0;
  private queuedOutputBytes = 0;
  private capturedFrames = 0;
  private clearedOutputFrames = 0;
  private staleOutputFrames = 0;
  private playedOutputFrames = 0;
  private ended = false;

  constructor({ maxInputFrames = 50, maxOutputBytes = 2_000_000 } = {}) {
    if (!Number.isInteger(maxInputFrames) || maxInputFrames < 1) {
      throw new Error("maxInputFrames must be a positive integer");
    }
    if (!Number.isInteger(maxOutputBytes) || maxOutputBytes < 1) {
      throw new Error("maxOutputBytes must be a positive integer");
    }
    this.maxInputFrames = maxInputFrames;
    this.maxOutputBytes = maxOutputBytes;
  }

  captureMicrophone(frame: Uint8Array): void {
    this.assertLive();
    if (frame.byteLength !== PCM16_FRAME_BYTES) {
      throw new Error("microphone frame must be exactly 20 ms PCM16 mono at 16 kHz");
    }
    if (this.inputFrames.length >= this.maxInputFrames) {
      throw new Error("microphone queue backpressure");
    }
    this.inputFrames.push(frame.slice());
    this.capturedFrames += 1;
  }

  consumeMicrophone(): Uint8Array | undefined {
    return this.inputFrames.shift();
  }

  startGeneration(generationId: string): void {
    this.assertLive();
    if (!/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/.test(generationId)) {
      throw new Error("generationId must be a bounded opaque identifier");
    }
    this.clearPlayback();
    this.activeGenerationId = generationId;
    this.lastQueuedOutputSequence = 0;
  }

  queueAssistantAudio(
    generationId: string,
    sequence: number,
    payload: Uint8Array,
  ): boolean {
    this.assertLive();
    if (generationId !== this.activeGenerationId) {
      this.staleOutputFrames += 1;
      return false;
    }
    if (!Number.isInteger(sequence) || sequence < 1 || payload.byteLength < 1) {
      throw new Error("assistant audio frame is invalid");
    }
    if (sequence <= this.lastQueuedOutputSequence) {
      throw new Error("assistant audio sequence must increase within a generation");
    }
    if (this.queuedOutputBytes + payload.byteLength > this.maxOutputBytes) {
      throw new Error("playback queue backpressure");
    }
    this.outputFrames.push({ generationId, sequence, payload: payload.slice() });
    this.queuedOutputBytes += payload.byteLength;
    this.lastQueuedOutputSequence = sequence;
    return true;
  }

  playNext(): Uint8Array | undefined {
    while (this.outputFrames.length > 0) {
      const frame = this.outputFrames.shift();
      if (!frame) return undefined;
      this.queuedOutputBytes -= frame.payload.byteLength;
      if (frame.generationId === this.activeGenerationId) {
        this.playedOutputFrames += 1;
        return frame.payload.slice();
      }
      this.staleOutputFrames += 1;
    }
    return undefined;
  }

  interrupt(generationId: string): number {
    if (generationId !== this.activeGenerationId) return 0;
    this.activeGenerationId = null;
    this.lastQueuedOutputSequence = 0;
    return this.clearPlayback();
  }

  clearPlayback(): number {
    const removed = this.outputFrames.length;
    this.outputFrames.length = 0;
    this.queuedOutputBytes = 0;
    this.clearedOutputFrames += removed;
    return removed;
  }

  hangup(): void {
    if (this.ended) return;
    this.activeGenerationId = null;
    this.lastQueuedOutputSequence = 0;
    this.clearPlayback();
    this.inputFrames.length = 0;
    this.ended = true;
  }

  snapshot(): DuplexLabSnapshot {
    return {
      activeGenerationId: this.activeGenerationId,
      capturedFrames: this.capturedFrames,
      queuedInputFrames: this.inputFrames.length,
      queuedOutputFrames: this.outputFrames.length,
      queuedOutputBytes: this.queuedOutputBytes,
      clearedOutputFrames: this.clearedOutputFrames,
      staleOutputFrames: this.staleOutputFrames,
      playedOutputFrames: this.playedOutputFrames,
      ended: this.ended,
    };
  }

  private assertLive(): void {
    if (this.ended) throw new Error("offline audio lab already ended");
  }
}
