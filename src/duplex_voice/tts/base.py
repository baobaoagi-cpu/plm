"""Provider-neutral one-generation-per-session TTS contract."""

from __future__ import annotations

import math
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from duplex_voice.tts.generation_state import GenerationToken


class TTSEventKind(StrEnum):
    CONNECTION_STARTED = "connection_started"
    CONNECTION_READY = "connection_ready"
    REQUEST_STARTED = "request_started"
    FIRST_AUDIO = "first_audio"
    AUDIO_CHUNK = "audio_chunk"
    INPUT_FINISHED = "input_finished"
    REQUEST_FINISHED = "request_finished"
    REQUEST_CANCELLED = "request_cancelled"
    REQUEST_FAILED = "request_failed"
    CONNECTION_CLOSED = "connection_closed"


@dataclass(frozen=True, slots=True)
class TTSEvent:
    kind: TTSEventKind
    token: GenerationToken
    timestamp_monotonic: float
    audio: bytes | None = field(default=None, repr=False)
    audio_sequence: int | None = None
    error_code: str | None = None

    def __post_init__(self) -> None:
        if self.timestamp_monotonic < 0 or not math.isfinite(self.timestamp_monotonic):
            raise ValueError("TTS timestamp must be finite and non-negative")
        if self.audio_sequence is not None and self.audio_sequence < 1:
            raise ValueError("audio sequence must be positive")


class GenerationTTS(Protocol):
    async def connect(self, token: GenerationToken) -> None: ...

    async def start_generation(self, token: GenerationToken) -> None: ...

    async def push_text(self, token: GenerationToken, text: str) -> None: ...

    async def finish_input(self, token: GenerationToken) -> None: ...

    async def cancel_generation(self, token: GenerationToken, reason: str) -> None: ...

    def events(self) -> AsyncIterator[TTSEvent]: ...

    async def close(self) -> None: ...


__all__ = ["GenerationTTS", "TTSEvent", "TTSEventKind"]
