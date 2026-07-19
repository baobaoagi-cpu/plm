import { useEffect } from "react";

interface DialToneProps {
  playing: boolean;
  maxBeeps?: number;
  onTimeout?: () => void;
}

export function DialTone({ playing, maxBeeps = 3, onTimeout }: DialToneProps) {
  useEffect(() => {
    if (!playing) return;

    const context = new AudioContext();
    let count = 0;
    const beep = () => {
      if (context.state === "closed") return;
      count += 1;
      if (count > maxBeeps) {
        onTimeout?.();
        return;
      }
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      oscillator.connect(gain);
      gain.connect(context.destination);
      oscillator.frequency.value = 440;
      gain.gain.setValueAtTime(0.12, context.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, context.currentTime + 0.35);
      oscillator.start();
      oscillator.stop(context.currentTime + 0.35);
    };
    beep();
    const timer = window.setInterval(beep, 1500);
    return () => {
      window.clearInterval(timer);
      void context.close();
    };
  }, [maxBeeps, onTimeout, playing]);

  return null;
}
