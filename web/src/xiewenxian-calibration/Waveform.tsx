import { useEffect, useRef } from "react";

interface WaveformProps {
  active: boolean;
  color?: string;
}

export function Waveform({ active, color = "#68d5a0" }: WaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;

    const width = 280;
    const height = 72;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    context.scale(dpr, dpr);

    let frame = 0;
    let phase = 0;
    const draw = () => {
      context.clearRect(0, 0, width, height);
      phase += active ? 0.08 : 0.02;
      for (let index = 0; index < 32; index += 1) {
        const amplitude = active
          ? Math.abs(Math.sin(phase + index * 0.34)) * 0.75 + 0.12
          : Math.abs(Math.sin(phase + index * 0.2)) * 0.12 + 0.05;
        const barHeight = amplitude * height * 0.7;
        context.globalAlpha = 0.35 + (1 - Math.abs(index - 16) / 16) * 0.65;
        context.fillStyle = color;
        context.fillRect(index * 8.75, (height - barHeight) / 2, 3, barHeight);
      }
      context.globalAlpha = 1;
      frame = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(frame);
  }, [active, color]);

  return <canvas aria-label={active ? "語音活動中" : "等待語音"} ref={canvasRef} />;
}
