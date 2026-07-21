"""Validated internal audio formats used by offline duplex tests."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum


class AudioEncoding(StrEnum):
    PCM_S16LE = "pcm_s16le"
    MP3 = "mp3"


@dataclass(frozen=True, slots=True)
class AudioFormat:
    encoding: AudioEncoding
    sample_rate: int
    channels: int
    sample_width_bytes: int | None

    def __post_init__(self) -> None:
        if self.sample_rate <= 0 or self.channels <= 0:
            raise ValueError("audio rate and channels must be positive")
        if self.encoding is AudioEncoding.PCM_S16LE and self.sample_width_bytes != 2:
            raise ValueError("pcm_s16le requires a two-byte sample width")
        if self.encoding is AudioEncoding.MP3 and self.sample_width_bytes is not None:
            raise ValueError("compressed MP3 has no fixed sample width")

    def pcm_duration_ms(self, byte_count: int) -> float:
        if self.encoding is not AudioEncoding.PCM_S16LE or self.sample_width_bytes is None:
            raise ValueError("duration from byte count is defined only for internal PCM")
        if byte_count <= 0:
            raise ValueError("byte_count must be positive")
        bytes_per_second = self.sample_rate * self.channels * self.sample_width_bytes
        duration = byte_count / bytes_per_second * 1_000
        if not math.isfinite(duration):
            raise ValueError("audio duration must be finite")
        return duration

    def pcm_bytes_for_duration(self, duration_ms: int) -> int:
        if self.encoding is not AudioEncoding.PCM_S16LE or self.sample_width_bytes is None:
            raise ValueError("byte sizing is defined only for internal PCM")
        if duration_ms <= 0:
            raise ValueError("duration_ms must be positive")
        numerator = self.sample_rate * self.channels * self.sample_width_bytes * duration_ms
        if numerator % 1_000:
            raise ValueError("duration does not align to a complete PCM sample")
        return numerator // 1_000


PCM16_MONO_16KHZ = AudioFormat(AudioEncoding.PCM_S16LE, 16_000, 1, 2)
PCM16_MONO_24KHZ = AudioFormat(AudioEncoding.PCM_S16LE, 24_000, 1, 2)
MINIMAX_MP3_24KHZ_MONO = AudioFormat(AudioEncoding.MP3, 24_000, 1, None)


__all__ = [
    "MINIMAX_MP3_24KHZ_MONO",
    "PCM16_MONO_16KHZ",
    "PCM16_MONO_24KHZ",
    "AudioEncoding",
    "AudioFormat",
]
