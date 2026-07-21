"""Stateful, provider-free protocol ordering and replay boundary."""

from __future__ import annotations

import hashlib
import re
from collections import deque
from dataclasses import dataclass

from duplex_voice.api.call_grant import CallGrantError, CallGrantValidator
from duplex_voice.api.protocol import (
    AudioInputFrame,
    CallEndFrame,
    CallStartFrame,
    ClientFrame,
    GenerationInterruptFrame,
    HeartbeatFrame,
    PlaybackDrainedFrame,
    ProtocolViolation,
    parse_client_frame,
)

_SAFE_GENERATION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")


class ProtocolIngressError(ValueError):
    """A redacted protocol-session rejection."""


@dataclass(frozen=True, slots=True)
class IngressDecision:
    frame: ClientFrame
    session_fingerprint: str
    accepted_sequence: int


class ProtocolSessionGate:
    """Enforce one ordered Protocol v1 stream for one verified call grant."""

    def __init__(
        self,
        session_id: str,
        subject_fingerprint: str,
        grant_validator: CallGrantValidator,
        *,
        message_window: int = 256,
    ) -> None:
        if message_window < 8 or message_window > 4_096:
            raise ValueError("message_window must be between 8 and 4096")
        self._session_id = session_id
        self._subject_fingerprint = subject_fingerprint
        self._grant_validator = grant_validator
        self._message_window = message_window
        self._recent_message_ids: deque[str] = deque()
        self._message_ids: set[str] = set()
        self._last_sequence = 0
        self._last_input_timestamp_ms = -1
        self._started = False
        self._ended = False
        self._active_generation_id: str | None = None

    def accept(self, raw: str | bytes) -> IngressDecision:
        if self._ended:
            raise ProtocolIngressError("call protocol stream already ended")
        try:
            frame = parse_client_frame(raw)
        except ProtocolViolation:
            raise ProtocolIngressError("invalid protocol frame") from None
        if frame.session_id != self._session_id:
            raise ProtocolIngressError("protocol session mismatch")
        if frame.message_id in self._message_ids:
            raise ProtocolIngressError("duplicate protocol message")
        expected_sequence = self._last_sequence + 1
        if frame.sequence != expected_sequence:
            raise ProtocolIngressError("protocol sequence is not contiguous")
        if not self._started:
            if not isinstance(frame, CallStartFrame):
                raise ProtocolIngressError("call.start must be the first frame")
            try:
                self._grant_validator.verify(
                    frame.payload.call_grant.get_secret_value(),
                    expected_session_id=self._session_id,
                    expected_subject_fingerprint=self._subject_fingerprint,
                )
            except CallGrantError:
                raise ProtocolIngressError("call grant rejected") from None
            self._started = True
        elif isinstance(frame, CallStartFrame):
            raise ProtocolIngressError("call.start cannot be repeated")
        elif isinstance(frame, AudioInputFrame):
            if frame.payload.payload_length != 640:
                raise ProtocolIngressError("audio frame length does not match 20 ms PCM")
            if frame.payload.timestamp_monotonic_ms <= self._last_input_timestamp_ms:
                raise ProtocolIngressError("audio timestamps must increase")
            self._last_input_timestamp_ms = frame.payload.timestamp_monotonic_ms
        elif isinstance(frame, GenerationInterruptFrame | PlaybackDrainedFrame):
            if frame.generation_id != self._active_generation_id:
                raise ProtocolIngressError("generation frame is stale or unknown")
        elif isinstance(frame, CallEndFrame):
            self._ended = True
            self._active_generation_id = None
        elif not isinstance(frame, HeartbeatFrame):
            raise ProtocolIngressError("unsupported protocol state")
        self._remember_message(frame.message_id)
        self._last_sequence = frame.sequence
        return IngressDecision(
            frame=frame,
            session_fingerprint=hashlib.sha256(self._session_id.encode()).hexdigest()[:12],
            accepted_sequence=frame.sequence,
        )

    def activate_generation(self, generation_id: str) -> None:
        if not self._started or self._ended:
            raise ProtocolIngressError("generation cannot activate outside a live call")
        if not _SAFE_GENERATION_ID.fullmatch(generation_id):
            raise ProtocolIngressError("generation identifier is invalid")
        self._active_generation_id = generation_id

    def clear_generation(self, generation_id: str) -> bool:
        if self._active_generation_id != generation_id:
            return False
        self._active_generation_id = None
        return True

    @property
    def retained_message_ids(self) -> int:
        return len(self._message_ids)

    @property
    def last_sequence(self) -> int:
        return self._last_sequence

    def _remember_message(self, message_id: str) -> None:
        self._recent_message_ids.append(message_id)
        self._message_ids.add(message_id)
        if len(self._recent_message_ids) > self._message_window:
            expired = self._recent_message_ids.popleft()
            self._message_ids.remove(expired)


__all__ = ["IngressDecision", "ProtocolIngressError", "ProtocolSessionGate"]
