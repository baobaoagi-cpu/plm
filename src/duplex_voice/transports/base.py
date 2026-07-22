"""Transport-only contract; it owns no dialogue or generation policy."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from duplex_voice.audio.queue import InputAudioFrame, OutputAudioChunk


class DuplexTransport(Protocol):
    async def connect(self) -> None: ...

    def input_audio(self) -> AsyncIterator[InputAudioFrame]: ...

    async def send_audio(self, chunk: OutputAudioChunk) -> None: ...

    async def clear_playback(self, generation_id: str) -> None: ...

    async def close(self) -> None: ...


__all__ = ["DuplexTransport"]
