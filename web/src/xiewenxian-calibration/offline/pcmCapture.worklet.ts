import { Pcm16Framer } from "./Pcm16Framer.js";

declare const sampleRate: number;
declare function registerProcessor(
  name: string,
  constructor: new () => AudioWorkletProcessor,
): void;
declare abstract class AudioWorkletProcessor {
  readonly port: MessagePort;
  abstract process(inputs: Float32Array[][]): boolean;
}

class PlmPcmCaptureProcessor extends AudioWorkletProcessor {
  private readonly framer = new Pcm16Framer(sampleRate);

  process(inputs: Float32Array[][]): boolean {
    const mono = inputs[0]?.[0];
    if (!mono) return true;
    for (const frame of this.framer.push(mono)) {
      this.port.postMessage({ type: "pcm.frame", payload: frame });
    }
    return true;
  }
}

registerProcessor("plm-pcm16-capture", PlmPcmCaptureProcessor);
