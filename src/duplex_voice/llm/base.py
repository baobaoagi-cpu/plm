"""Provider-neutral cancellable streaming LLM contract."""

from __future__ import annotations

import asyncio
import math
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True, slots=True)
class Message:
    role: MessageRole
    content: str = field(repr=False)

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError("message content must not be empty")


class LLMEventKind(StrEnum):
    REQUEST_STARTED = "request_started"
    FIRST_TOKEN = "first_token"
    TEXT_DELTA = "text_delta"
    TOOL_CALL = "tool_call"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class LLMEvent:
    kind: LLMEventKind
    generation_id: str
    timestamp_monotonic: float
    display_text: str | None = field(default=None, repr=False)
    speak_text: str | None = field(default=None, repr=False)
    error_code: str | None = None

    def __post_init__(self) -> None:
        if not self.generation_id:
            raise ValueError("generation_id must not be empty")
        if self.timestamp_monotonic < 0 or not math.isfinite(self.timestamp_monotonic):
            raise ValueError("LLM timestamp must be finite and non-negative")


class CancellationToken:
    """Small provider-independent cancellation signal for stream adapters."""

    def __init__(self) -> None:
        self._event = asyncio.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    async def wait(self) -> None:
        await self._event.wait()


class StreamingLLM(Protocol):
    def generate(
        self,
        messages: Sequence[Message],
        generation_id: str,
        cancel_token: CancellationToken,
    ) -> AsyncIterator[LLMEvent]: ...

    async def close(self) -> None: ...


__all__ = [
    "CancellationToken",
    "LLMEvent",
    "LLMEventKind",
    "Message",
    "MessageRole",
    "StreamingLLM",
]
