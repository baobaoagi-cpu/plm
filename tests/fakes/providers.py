"""Deterministic provider doubles; never presented as real provider evidence."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Callable, Sequence
from dataclasses import dataclass

from duplex_voice.audio.queue import InputAudioFrame
from duplex_voice.llm.base import (
    CancellationToken,
    LLMEvent,
    LLMEventKind,
    Message,
)
from duplex_voice.providers.faults import (
    ProviderAdapterError,
    ProviderErrorCode,
    ProviderFailure,
)
from duplex_voice.stt.base import STTEvent, STTEventKind
from duplex_voice.tts.base import TTSEvent, TTSEventKind
from duplex_voice.tts.generation_guard import GenerationGuard
from duplex_voice.tts.generation_state import GenerationToken


@dataclass(frozen=True, slots=True)
class FaultPlan:
    fail_connect: bool = False
    fail_after_items: int | None = None
    stall_connect: bool = False


def _failure(provider: str, operation: str) -> ProviderAdapterError:
    return ProviderAdapterError(
        ProviderFailure(
            provider=provider,
            operation=operation,
            code=ProviderErrorCode.INTERNAL_ERROR,
            retryable=False,
            trace_id="synthetic-trace",
        )
    )


class FakeStreamingSTT:
    def __init__(
        self,
        fault: FaultPlan | None = None,
        *,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._fault = fault or FaultPlan()
        self._monotonic = monotonic
        self._events: asyncio.Queue[STTEvent | None] = asyncio.Queue()
        self.connected = False
        self.closed = False
        self.received_frames = 0

    async def connect(self) -> None:
        if self._fault.stall_connect:
            await asyncio.Event().wait()
        if self._fault.fail_connect:
            raise _failure("fake_stt", "connect")
        self.connected = True

    async def push_audio(self, frame: InputAudioFrame) -> None:
        if not self.connected or self.closed:
            raise _failure("fake_stt", "push_audio")
        assert frame.payload
        self.received_frames += 1
        if (
            self._fault.fail_after_items is not None
            and self.received_frames > self._fault.fail_after_items
        ):
            await self._events.put(
                STTEvent(
                    STTEventKind.ERROR,
                    self._monotonic(),
                    error_code="synthetic_failure",
                )
            )

    async def emit_transcript(self, text: str, *, final: bool, revision: int) -> None:
        await self._events.put(
            STTEvent(
                STTEventKind.FINAL_TRANSCRIPT if final else STTEventKind.PARTIAL_TRANSCRIPT,
                self._monotonic(),
                revision=revision,
                transcript=text,
            )
        )

    async def events(self) -> AsyncIterator[STTEvent]:
        while True:
            event = await self._events.get()
            if event is None:
                return
            yield event

    async def close(self) -> None:
        if not self.closed:
            self.closed = True
            await self._events.put(None)


class FakeStreamingLLM:
    def __init__(
        self,
        deltas: Sequence[str],
        fault: FaultPlan | None = None,
        *,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._deltas = tuple(deltas)
        self._fault = fault or FaultPlan()
        self._monotonic = monotonic
        self.closed = False

    async def generate(
        self,
        messages: Sequence[Message],
        generation_id: str,
        cancel_token: CancellationToken,
    ) -> AsyncIterator[LLMEvent]:
        if not messages:
            raise ValueError("messages must not be empty")
        yield LLMEvent(LLMEventKind.REQUEST_STARTED, generation_id, self._monotonic())
        for index, delta in enumerate(self._deltas, start=1):
            if cancel_token.is_cancelled:
                yield LLMEvent(LLMEventKind.CANCELLED, generation_id, self._monotonic())
                return
            if self._fault.fail_after_items is not None and index > self._fault.fail_after_items:
                yield LLMEvent(
                    LLMEventKind.FAILED,
                    generation_id,
                    self._monotonic(),
                    error_code="synthetic_failure",
                )
                return
            if index == 1:
                yield LLMEvent(LLMEventKind.FIRST_TOKEN, generation_id, self._monotonic())
            yield LLMEvent(
                LLMEventKind.TEXT_DELTA,
                generation_id,
                self._monotonic(),
                display_text=delta,
                speak_text=delta,
            )
            await asyncio.sleep(0)
        yield LLMEvent(LLMEventKind.COMPLETED, generation_id, self._monotonic())

    async def close(self) -> None:
        self.closed = True


class FakeGenerationTTS:
    def __init__(
        self,
        guard: GenerationGuard,
        fault: FaultPlan | None = None,
        *,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._guard = guard
        self._fault = fault or FaultPlan()
        self._monotonic = monotonic
        self._events: asyncio.Queue[TTSEvent | None] = asyncio.Queue()
        self._token: GenerationToken | None = None
        self._text_items = 0
        self.closed = False

    async def connect(self, token: GenerationToken) -> None:
        if self._fault.stall_connect:
            await asyncio.Event().wait()
        if self._fault.fail_connect:
            raise _failure("fake_tts", "connect")
        if self._token is not None and self._token != token:
            raise _failure("fake_tts", "connection_reuse")
        self._token = token
        await self._events.put(TTSEvent(TTSEventKind.CONNECTION_READY, token, self._monotonic()))

    async def start_generation(self, token: GenerationToken) -> None:
        if self._token != token or not self._guard.should_accept(token):
            raise _failure("fake_tts", "start_generation")
        await self._events.put(TTSEvent(TTSEventKind.REQUEST_STARTED, token, self._monotonic()))

    async def push_text(self, token: GenerationToken, text: str) -> None:
        if self._token != token or not self._guard.should_accept(token):
            raise _failure("fake_tts", "push_text")
        if not text:
            raise ValueError("text must not be empty")
        self._text_items += 1
        if (
            self._fault.fail_after_items is not None
            and self._text_items > self._fault.fail_after_items
        ):
            await self._events.put(
                TTSEvent(
                    TTSEventKind.REQUEST_FAILED,
                    token,
                    self._monotonic(),
                    error_code="synthetic_failure",
                )
            )

    async def emit_audio(self, token: GenerationToken, audio: bytes, *, sequence: int) -> bool:
        if self._token != token or not self._guard.should_accept(token):
            return False
        await self._events.put(
            TTSEvent(
                TTSEventKind.AUDIO_CHUNK,
                token,
                self._monotonic(),
                audio=audio,
                audio_sequence=sequence,
            )
        )
        return True

    async def finish_input(self, token: GenerationToken) -> None:
        if self._token != token:
            raise _failure("fake_tts", "finish_input")
        await self._events.put(TTSEvent(TTSEventKind.INPUT_FINISHED, token, self._monotonic()))

    async def cancel_generation(self, token: GenerationToken, reason: str) -> None:
        if not reason:
            raise ValueError("reason must not be empty")
        self._guard.cancel(token, reason)
        await self._events.put(TTSEvent(TTSEventKind.REQUEST_CANCELLED, token, self._monotonic()))

    async def events(self) -> AsyncIterator[TTSEvent]:
        while True:
            event = await self._events.get()
            if event is None:
                return
            yield event

    async def close(self) -> None:
        if not self.closed:
            self.closed = True
            await self._events.put(None)


__all__ = [
    "FakeGenerationTTS",
    "FakeStreamingLLM",
    "FakeStreamingSTT",
    "FaultPlan",
]
