"""Deterministic offline harness proving independent listen and speak tracks."""

from __future__ import annotations

import time
from collections.abc import Callable

from duplex_voice.audio.queue import (
    BoundedInputAudioQueue,
    GenerationAudioQueue,
    InputAudioFrame,
    OutputAudioChunk,
)
from duplex_voice.tts.generation_guard import GenerationGuard
from duplex_voice.tts.generation_state import GenerationToken


class OfflineDuplexHarness:
    """Exercise duplex invariants without Pipecat, provider, transport, or real audio."""

    def __init__(
        self,
        session_id: str,
        *,
        input_max_pending_ms: float = 1_000.0,
        output_max_pending_ms: float = 2_000.0,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.session_id = session_id
        self.guard = GenerationGuard(monotonic=monotonic)
        self.input_queue = BoundedInputAudioQueue(max_pending_ms=input_max_pending_ms)
        self.output_queue = GenerationAudioQueue(
            session_id,
            self.guard,
            max_pending_ms=output_max_pending_ms,
            monotonic=monotonic,
        )
        self._monotonic = monotonic

    def start_generation(self) -> GenerationToken:
        if self.guard.get_active(self.session_id) is None:
            token = self.guard.create(self.session_id)
            self.guard.activate(token)
            return token
        return self.guard.replace_active(self.session_id, "newer_generation")

    def receive_microphone(
        self, *, sequence: int, payload: bytes, duration_ms: float
    ) -> None:
        self.input_queue.enqueue(
            InputAudioFrame(
                sequence=sequence,
                payload=payload,
                duration_ms=duration_ms,
                captured_at_monotonic=self._monotonic(),
            )
        )

    def receive_assistant_audio(
        self,
        token: GenerationToken,
        *,
        sequence: int,
        payload: bytes,
        duration_ms: float,
    ) -> bool:
        return self.output_queue.enqueue(
            self.output_queue.make_chunk(
                token,
                sequence=sequence,
                payload=payload,
                duration_ms=duration_ms,
            )
        )

    def interrupt(self, token: GenerationToken) -> int:
        """Stop local admission and clear playback without awaiting provider acknowledgement."""

        self.guard.begin_cancel(token, "user_interruption")
        removed = self.output_queue.clear_generation(token)
        self.guard.mark_cancelled(token)
        return removed

    def hangup(self) -> None:
        active = self.guard.get_active(self.session_id)
        if active is not None:
            self.guard.cancel(active, "call_ended")
        self.output_queue.clear_all()
        self.input_queue.clear()

    def play_next(self) -> OutputAudioChunk | None:
        return self.output_queue.pop_playable()


__all__ = ["OfflineDuplexHarness"]
