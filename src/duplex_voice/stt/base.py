"""Provider-neutral streaming STT contract."""

from __future__ import annotations

import math
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from duplex_voice.audio.queue import InputAudioFrame


class STTEventKind(StrEnum):
    SPEECH_STARTED = "speech_started"
    PARTIAL_TRANSCRIPT = "partial_transcript"
    FINAL_TRANSCRIPT = "final_transcript"
    SPEECH_ENDED = "speech_ended"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class STTEvent:
    kind: STTEventKind
    timestamp_monotonic: float
    revision: int = 0
    transcript: str | None = field(default=None, repr=False)
    error_code: str | None = None

    def __post_init__(self) -> None:
        if self.timestamp_monotonic < 0 or not math.isfinite(self.timestamp_monotonic):
            raise ValueError("STT timestamp must be finite and non-negative")
        if self.revision < 0:
            raise ValueError("STT revision must be non-negative")


class StreamingSTT(Protocol):
    async def connect(self) -> None: ...

    async def push_audio(self, frame: InputAudioFrame) -> None: ...

    def events(self) -> AsyncIterator[STTEvent]: ...

    async def close(self) -> None: ...


__all__ = ["STTEvent", "STTEventKind", "StreamingSTT"]
