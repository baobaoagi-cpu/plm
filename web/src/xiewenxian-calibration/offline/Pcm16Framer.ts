const TARGET_SAMPLE_RATE = 16_000;
const FRAME_SAMPLES = 320;
const FRAME_BYTES = FRAME_SAMPLES * 2;

export class Pcm16Framer {
  readonly sourceSampleRate: number;
  private phase = 0;
  private readonly pending: number[] = [];

  constructor(sourceSampleRate: number) {
    if (!Number.isInteger(sourceSampleRate) || sourceSampleRate < TARGET_SAMPLE_RATE) {
      throw new Error("source sample rate must be an integer at or above 16 kHz");
    }
    this.sourceSampleRate = sourceSampleRate;
  }

  push(samples: Float32Array): Uint8Array[] {
    const frames: Uint8Array[] = [];
    for (const sample of samples) {
      this.phase += TARGET_SAMPLE_RATE;
      if (this.phase < this.sourceSampleRate) continue;
      this.phase -= this.sourceSampleRate;
      this.pending.push(floatToPcm16(sample));
      if (this.pending.length === FRAME_SAMPLES) {
        frames.push(encodeLittleEndian(this.pending));
        this.pending.length = 0;
      }
    }
    return frames;
  }

  reset(): void {
    this.phase = 0;
    this.pending.length = 0;
  }

  get pendingSamples(): number {
    return this.pending.length;
  }
}

function floatToPcm16(value: number): number {
  const finite = Number.isFinite(value) ? value : 0;
  const clamped = Math.max(-1, Math.min(1, finite));
  return clamped < 0 ? Math.round(clamped * 32_768) : Math.round(clamped * 32_767);
}

function encodeLittleEndian(samples: readonly number[]): Uint8Array {
  const frame = new Uint8Array(FRAME_BYTES);
  const view = new DataView(frame.buffer);
  samples.forEach((sample, index) => view.setInt16(index * 2, sample, true));
  return frame;
}

export const PCM16_FRAME_BYTES = FRAME_BYTES;
export const PCM16_FRAME_DURATION_MS = 20;
export const PCM16_SAMPLE_RATE = TARGET_SAMPLE_RATE;
