"""Independent bounded input and generation-aware output audio queues."""

from __future__ import annotations

import math
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

from duplex_voice.tts.generation_guard import GenerationGuard
from duplex_voice.tts.generation_state import GenerationToken


class AudioBackpressureError(RuntimeError):
    """Raised before a bounded queue can grow beyond its configured limit."""


@dataclass(frozen=True, slots=True)
class InputAudioFrame:
    sequence: int
    payload: bytes = field(repr=False)
    duration_ms: float
    captured_at_monotonic: float


@dataclass(frozen=True, slots=True)
class OutputAudioChunk:
    token: GenerationToken
    sequence: int
    payload: bytes = field(repr=False)
    duration_ms: float
    received_at_monotonic: float


@dataclass(frozen=True, slots=True)
class AudioQueueStats:
    queued_items: int
    pending_ms: float
    pending_bytes: int
    accepted_items: int
    played_items: int
    cleared_items: int
    stale_items_dropped: int
    backpressure_rejections: int


def _validate_audio_payload(sequence: int, payload: bytes, duration_ms: float) -> None:
    if sequence < 1:
        raise ValueError("audio sequence must be positive")
    if not payload:
        raise ValueError("audio payload must not be empty")
    if duration_ms <= 0 or not math.isfinite(duration_ms):
        raise ValueError("audio duration must be finite and positive")


class BoundedInputAudioQueue:
    """Bound microphone buffering independently from assistant playback."""

    def __init__(self, *, max_pending_ms: float = 1_000.0) -> None:
        if max_pending_ms <= 0 or not math.isfinite(max_pending_ms):
            raise ValueError("max_pending_ms must be finite and positive")
        self._max_pending_ms = max_pending_ms
        self._lock = threading.RLock()
        self._items: deque[InputAudioFrame] = deque()
        self._pending_ms = 0.0
        self._pending_bytes = 0
        self._accepted = 0
        self._consumed = 0
        self._cleared = 0
        self._backpressure = 0

    def enqueue(self, frame: InputAudioFrame) -> None:
        _validate_audio_payload(frame.sequence, frame.payload, frame.duration_ms)
        with self._lock:
            if self._pending_ms + frame.duration_ms > self._max_pending_ms:
                self._backpressure += 1
                raise AudioBackpressureError("input audio queue limit reached")
            self._items.append(frame)
            self._pending_ms += frame.duration_ms
            self._pending_bytes += len(frame.payload)
            self._accepted += 1

    def pop(self) -> InputAudioFrame | None:
        with self._lock:
            if not self._items:
                return None
            frame = self._items.popleft()
            self._pending_ms -= frame.duration_ms
            self._pending_bytes -= len(frame.payload)
            self._consumed += 1
            return frame

    def clear(self) -> int:
        with self._lock:
            count = len(self._items)
            self._items.clear()
            self._pending_ms = 0.0
            self._pending_bytes = 0
            self._cleared += count
            return count

    def stats(self) -> AudioQueueStats:
        with self._lock:
            return AudioQueueStats(
                queued_items=len(self._items),
                pending_ms=self._pending_ms,
                pending_bytes=self._pending_bytes,
                accepted_items=self._accepted,
                played_items=self._consumed,
                cleared_items=self._cleared,
                stale_items_dropped=0,
                backpressure_rejections=self._backpressure,
            )


class GenerationAudioQueue:
    """Reject stale output both when enqueued and immediately before playback."""

    def __init__(
        self,
        session_id: str,
        guard: GenerationGuard,
        *,
        max_pending_ms: float = 2_000.0,
        max_pending_bytes: int = 2_000_000,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if not session_id:
            raise ValueError("session_id must not be empty")
        if max_pending_ms <= 0 or not math.isfinite(max_pending_ms):
            raise ValueError("max_pending_ms must be finite and positive")
        if max_pending_bytes <= 0:
            raise ValueError("max_pending_bytes must be positive")
        self._session_id = session_id
        self._guard = guard
        self._max_pending_ms = max_pending_ms
        self._max_pending_bytes = max_pending_bytes
        self._monotonic = monotonic
        self._lock = threading.RLock()
        self._items: deque[OutputAudioChunk] = deque()
        self._pending_ms = 0.0
        self._pending_bytes = 0
        self._accepted = 0
        self._played = 0
        self._cleared = 0
        self._stale = 0
        self._backpressure = 0

    def make_chunk(
        self,
        token: GenerationToken,
        *,
        sequence: int,
        payload: bytes,
        duration_ms: float,
    ) -> OutputAudioChunk:
        return OutputAudioChunk(
            token=token,
            sequence=sequence,
            payload=payload,
            duration_ms=duration_ms,
            received_at_monotonic=self._monotonic(),
        )

    def enqueue(self, chunk: OutputAudioChunk) -> bool:
        _validate_audio_payload(chunk.sequence, chunk.payload, chunk.duration_ms)
        if chunk.token.session_id != self._session_id:
            raise ValueError("output chunk belongs to another session")
        if not self._guard.should_accept(chunk.token):
            with self._lock:
                self._stale += 1
            return False
        with self._lock:
            if (
                self._pending_ms + chunk.duration_ms > self._max_pending_ms
                or self._pending_bytes + len(chunk.payload) > self._max_pending_bytes
            ):
                self._backpressure += 1
                raise AudioBackpressureError("output audio queue limit reached")
            self._items.append(chunk)
            self._pending_ms += chunk.duration_ms
            self._pending_bytes += len(chunk.payload)
            self._accepted += 1
            return True

    def pop_playable(self) -> OutputAudioChunk | None:
        """Perform the hard generation check at the final pre-playback boundary."""

        with self._lock:
            while self._items:
                chunk = self._items.popleft()
                self._pending_ms -= chunk.duration_ms
                self._pending_bytes -= len(chunk.payload)
                if self._guard.should_accept(chunk.token):
                    self._played += 1
                    return chunk
                self._stale += 1
            return None

    def clear_generation(self, token: GenerationToken) -> int:
        with self._lock:
            retained: deque[OutputAudioChunk] = deque()
            removed = 0
            while self._items:
                chunk = self._items.popleft()
                if chunk.token == token:
                    self._pending_ms -= chunk.duration_ms
                    self._pending_bytes -= len(chunk.payload)
                    removed += 1
                else:
                    retained.append(chunk)
            self._items = retained
            self._cleared += removed
            return removed

    def clear_all(self) -> int:
        with self._lock:
            removed = len(self._items)
            self._items.clear()
            self._pending_ms = 0.0
            self._pending_bytes = 0
            self._cleared += removed
            return removed

    def stats(self) -> AudioQueueStats:
        with self._lock:
            return AudioQueueStats(
                queued_items=len(self._items),
                pending_ms=max(0.0, self._pending_ms),
                pending_bytes=max(0, self._pending_bytes),
                accepted_items=self._accepted,
                played_items=self._played,
                cleared_items=self._cleared,
                stale_items_dropped=self._stale,
                backpressure_rejections=self._backpressure,
            )


__all__ = [
    "AudioBackpressureError",
    "AudioQueueStats",
    "BoundedInputAudioQueue",
    "GenerationAudioQueue",
    "InputAudioFrame",
    "OutputAudioChunk",
]
