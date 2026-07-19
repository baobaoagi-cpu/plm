"""Thread-safe, provider-independent hard gate for generation-scoped data.

The public methods are synchronous because every critical section is short, bounded, in-memory
work protected by an ``RLock``. They are safe to call from an asyncio runtime and are also safe
when several worker threads enter concurrently. Event sinks run only after the lock is released.
"""

from __future__ import annotations

import hashlib
import math
import re
import threading
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import replace

from duplex_voice.tts.generation_state import (
    ALLOWED_GENERATION_TRANSITIONS,
    TERMINAL_GENERATION_STATES,
    ActiveGenerationConflictError,
    GenerationGuardError,
    GenerationMetadataError,
    GenerationNotAcceptingError,
    GenerationRecord,
    GenerationSessionMismatchError,
    GenerationState,
    GenerationStateChanged,
    GenerationToken,
    InvalidGenerationTransitionError,
    UnknownGenerationError,
)

type MetadataScalar = str | int | float | bool | None
type EventSink = Callable[[GenerationStateChanged], None]

_SAFE_SESSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SAFE_REASON_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_SAFE_METADATA_KEY_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_SENSITIVE_METADATA_FRAGMENTS = frozenset(
    {
        "api_key",
        "authorization",
        "audio",
        "bearer",
        "credential",
        "prompt",
        "secret",
        "text",
        "token",
        "transcript",
        "voice_id",
    }
)


class GenerationGuard:
    """Own generation lifecycle, active selection, late-data rejection, and cleanup."""

    def __init__(
        self,
        *,
        terminal_ttl_s: float = 300.0,
        max_terminal_records: int = 1_000,
        event_sink: EventSink | None = None,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if terminal_ttl_s < 0 or not math.isfinite(terminal_ttl_s):
            raise ValueError("terminal_ttl_s must be finite and non-negative")
        if max_terminal_records < 0:
            raise ValueError("max_terminal_records must be non-negative")
        self._terminal_ttl_s = terminal_ttl_s
        self._max_terminal_records = max_terminal_records
        self._event_sink = event_sink
        self._monotonic = monotonic
        self._lock = threading.RLock()
        self._records: dict[str, GenerationRecord] = {}
        self._active_by_session: dict[str, GenerationToken] = {}
        self._sequences: dict[str, int] = {}

    def create(
        self, session_id: str, metadata: Mapping[str, object] | None = None
    ) -> GenerationToken:
        self._validate_session_id(session_id)
        safe_metadata = self._sanitize_metadata(metadata)
        with self._lock:
            sequence = self._sequences.get(session_id, 0) + 1
            self._sequences[session_id] = sequence
            generation_id = self._new_generation_id_locked()
            token = GenerationToken(session_id, generation_id, sequence)
            now = self._monotonic()
            self._records[generation_id] = GenerationRecord(
                token=token,
                state=GenerationState.CREATED,
                created_at_monotonic=now,
                metadata=safe_metadata,
            )
            event = self._event(token, None, GenerationState.CREATED, None, now)
        self._publish((event,))
        return token

    def activate(self, token: GenerationToken) -> None:
        with self._lock:
            record = self._resolve_locked(token)
            active = self._active_by_session.get(token.session_id)
            if active is not None and active != token:
                raise ActiveGenerationConflictError(
                    "session already has an active generation; supersede or cancel it first"
                )
            event = self._transition_locked(record, GenerationState.ACTIVE, None)
        self._publish((event,))

    def begin_cancel(self, token: GenerationToken, reason: str) -> bool:
        reason = self._validate_reason(reason)
        with self._lock:
            record = self._resolve_locked(token)
            if record.state in TERMINAL_GENERATION_STATES:
                return False
            target = (
                GenerationState.CANCELLED
                if record.state is GenerationState.CREATED
                else GenerationState.CANCELLING
            )
            event = self._transition_locked(record, target, reason)
        self._publish((event,))
        return True

    def mark_cancelled(self, token: GenerationToken) -> bool:
        with self._lock:
            record = self._resolve_locked(token)
            if record.state is GenerationState.CANCELLED:
                return False
            if record.state in TERMINAL_GENERATION_STATES:
                return False
            event = self._transition_locked(
                record, GenerationState.CANCELLED, record.cancel_reason
            )
        self._publish((event,))
        return True

    def cancel(self, token: GenerationToken, reason: str) -> bool:
        """Atomically complete the local cancellation lifecycle.

        An active generation emits ACTIVE -> CANCELLING -> CANCELLED. Provider-side cancellation is
        deliberately outside this class; local acceptance stops at the first transition.
        """

        reason = self._validate_reason(reason)
        with self._lock:
            record = self._resolve_locked(token)
            if record.state in TERMINAL_GENERATION_STATES:
                return False
            events: list[GenerationStateChanged] = []
            if record.state is GenerationState.ACTIVE:
                events.append(
                    self._transition_locked(record, GenerationState.CANCELLING, reason)
                )
                events.append(
                    self._transition_locked(record, GenerationState.CANCELLED, reason)
                )
            elif record.state is GenerationState.CREATED:
                events.append(
                    self._transition_locked(record, GenerationState.CANCELLED, reason)
                )
            elif record.state is GenerationState.CANCELLING:
                events.append(
                    self._transition_locked(
                        record, GenerationState.CANCELLED, record.cancel_reason or reason
                    )
                )
            else:
                raise InvalidGenerationTransitionError("generation cannot be cancelled")
        self._publish(events)
        return True

    def complete(self, token: GenerationToken) -> bool:
        return self._finish(token, GenerationState.COMPLETED, None)

    def fail(self, token: GenerationToken, reason: str) -> bool:
        return self._finish(token, GenerationState.FAILED, self._validate_reason(reason))

    def supersede(self, token: GenerationToken, reason: str) -> bool:
        return self._finish(token, GenerationState.SUPERSEDED, self._validate_reason(reason))

    def is_active(self, token: GenerationToken) -> bool:
        return self.should_accept(token)

    def is_terminal(self, token: GenerationToken) -> bool:
        with self._lock:
            return self._resolve_locked(token).state in TERMINAL_GENERATION_STATES

    def should_accept(self, token: GenerationToken) -> bool:
        """Return False, without raising, for stale, terminal, mismatched, or unknown data."""

        with self._lock:
            try:
                record = self._resolve_locked(token)
            except GenerationGuardError:
                return False
            return (
                record.state is GenerationState.ACTIVE
                and self._active_by_session.get(token.session_id) == token
            )

    def assert_accepting(self, token: GenerationToken) -> None:
        with self._lock:
            record = self._resolve_locked(token)
            if (
                record.state is not GenerationState.ACTIVE
                or self._active_by_session.get(token.session_id) != token
            ):
                raise GenerationNotAcceptingError("generation is not accepting data")

    def get_state(self, token: GenerationToken) -> GenerationState:
        with self._lock:
            return self._resolve_locked(token).state

    def get_active(self, session_id: str) -> GenerationToken | None:
        self._validate_session_id(session_id)
        with self._lock:
            return self._active_by_session.get(session_id)

    def cancel_active(self, session_id: str, reason: str) -> GenerationToken | None:
        self._validate_session_id(session_id)
        with self._lock:
            token = self._active_by_session.get(session_id)
        if token is None:
            return None
        self.cancel(token, reason)
        return token

    def replace_active(
        self,
        session_id: str,
        reason: str,
        metadata: Mapping[str, object] | None = None,
    ) -> GenerationToken:
        """Atomically supersede the active generation and activate a new one."""

        self._validate_session_id(session_id)
        reason = self._validate_reason(reason)
        safe_metadata = self._sanitize_metadata(metadata)
        with self._lock:
            events: list[GenerationStateChanged] = []
            old_token = self._active_by_session.get(session_id)
            if old_token is not None:
                old_record = self._resolve_locked(old_token)
                events.append(
                    self._transition_locked(old_record, GenerationState.SUPERSEDED, reason)
                )

            sequence = self._sequences.get(session_id, 0) + 1
            self._sequences[session_id] = sequence
            generation_id = self._new_generation_id_locked()
            token = GenerationToken(session_id, generation_id, sequence)
            now = self._monotonic()
            record = GenerationRecord(
                token=token,
                state=GenerationState.CREATED,
                created_at_monotonic=now,
                metadata=safe_metadata,
            )
            self._records[generation_id] = record
            events.append(self._event(token, None, GenerationState.CREATED, None, now))
            events.append(self._transition_locked(record, GenerationState.ACTIVE, None))
        self._publish(events)
        return token

    def cleanup(self, cutoff_monotonic: float | None = None) -> int:
        """Delete expired/excess terminal records and never delete live records."""

        if cutoff_monotonic is not None and not math.isfinite(cutoff_monotonic):
            raise ValueError("cutoff_monotonic must be finite")
        with self._lock:
            cutoff = (
                cutoff_monotonic
                if cutoff_monotonic is not None
                else self._monotonic() - self._terminal_ttl_s
            )
            terminal = [
                record
                for record in self._records.values()
                if record.state in TERMINAL_GENERATION_STATES
                and record.finished_at_monotonic is not None
            ]
            remove_ids = {
                record.token.generation_id
                for record in terminal
                if record.finished_at_monotonic is not None
                and record.finished_at_monotonic <= cutoff
            }
            remaining = sorted(
                (r for r in terminal if r.token.generation_id not in remove_ids),
                key=lambda record: record.finished_at_monotonic or 0.0,
            )
            excess = max(0, len(remaining) - self._max_terminal_records)
            remove_ids.update(r.token.generation_id for r in remaining[:excess])
            for generation_id in remove_ids:
                del self._records[generation_id]
            return len(remove_ids)

    @property
    def record_count(self) -> int:
        with self._lock:
            return len(self._records)

    def snapshot(self) -> dict[str, object]:
        """Return a deterministic debug view that intentionally omits all metadata."""

        with self._lock:
            records = sorted(self._records.values(), key=lambda record: record.token.generation_id)
            return {
                "record_count": len(records),
                "active_count": len(self._active_by_session),
                "records": [
                    {
                        "session_id": self._safe_session_id(record.token.session_id),
                        "generation_id": record.token.generation_id,
                        "sequence": record.token.sequence,
                        "state": record.state.value,
                        "created_at_monotonic": record.created_at_monotonic,
                        "activated_at_monotonic": record.activated_at_monotonic,
                        "finished_at_monotonic": record.finished_at_monotonic,
                        "cancel_reason": record.cancel_reason,
                        "failure_reason": record.failure_reason,
                    }
                    for record in records
                ],
            }

    def get_record(self, token: GenerationToken) -> GenerationRecord:
        """Return a detached record copy for diagnostics without exposing internal mutation."""

        with self._lock:
            record = self._resolve_locked(token)
            return replace(record, metadata=dict(record.metadata))

    def _finish(
        self, token: GenerationToken, target: GenerationState, reason: str | None
    ) -> bool:
        with self._lock:
            record = self._resolve_locked(token)
            if record.state in TERMINAL_GENERATION_STATES:
                return False
            event = self._transition_locked(record, target, reason)
        self._publish((event,))
        return True

    def _transition_locked(
        self,
        record: GenerationRecord,
        target: GenerationState,
        reason: str | None,
    ) -> GenerationStateChanged:
        old_state = record.state
        if target not in ALLOWED_GENERATION_TRANSITIONS[old_state]:
            raise InvalidGenerationTransitionError(
                f"invalid generation transition {old_state.value} -> {target.value}"
            )
        now = self._monotonic()
        record.state = target
        if target is GenerationState.ACTIVE:
            active = self._active_by_session.get(record.token.session_id)
            if active is not None and active != record.token:
                raise ActiveGenerationConflictError("session already has an active generation")
            record.activated_at_monotonic = now
            self._active_by_session[record.token.session_id] = record.token
        if old_state is GenerationState.ACTIVE and target is not GenerationState.ACTIVE:
            if self._active_by_session.get(record.token.session_id) == record.token:
                del self._active_by_session[record.token.session_id]
        if target in {GenerationState.CANCELLING, GenerationState.CANCELLED}:
            record.cancel_reason = reason
        elif target is GenerationState.SUPERSEDED:
            record.cancel_reason = reason
        elif target is GenerationState.FAILED:
            record.failure_reason = reason
        if target in TERMINAL_GENERATION_STATES:
            record.finished_at_monotonic = now
        return self._event(record.token, old_state, target, reason, now)

    def _resolve_locked(self, token: GenerationToken) -> GenerationRecord:
        record = self._records.get(token.generation_id)
        if record is None:
            raise UnknownGenerationError("unknown generation")
        if record.token.session_id != token.session_id:
            raise GenerationSessionMismatchError("generation session mismatch")
        if record.token.sequence != token.sequence:
            raise UnknownGenerationError("unknown generation token")
        return record

    def _new_generation_id_locked(self) -> str:
        while True:
            generation_id = str(uuid.uuid4())
            if generation_id not in self._records:
                return generation_id

    def _event(
        self,
        token: GenerationToken,
        old_state: GenerationState | None,
        new_state: GenerationState,
        reason: str | None,
        now: float,
    ) -> GenerationStateChanged:
        return GenerationStateChanged(
            event="generation_state_changed",
            session_id=self._safe_session_id(token.session_id),
            generation_id=token.generation_id,
            from_state=old_state,
            to_state=new_state,
            reason=reason,
            timestamp_monotonic_ms=int(now * 1_000),
        )

    def _publish(
        self, events: list[GenerationStateChanged] | tuple[GenerationStateChanged, ...]
    ) -> None:
        if self._event_sink is None:
            return
        for event in events:
            self._event_sink(event)

    @staticmethod
    def _validate_session_id(session_id: str) -> None:
        if not _SAFE_SESSION_RE.fullmatch(session_id):
            raise ValueError("session_id must be a non-empty safe opaque identifier")

    @staticmethod
    def _validate_reason(reason: str) -> str:
        if not _SAFE_REASON_RE.fullmatch(reason):
            raise ValueError("reason must be a safe machine-readable code")
        return reason

    @staticmethod
    def _sanitize_metadata(metadata: Mapping[str, object] | None) -> dict[str, object]:
        if metadata is None:
            return {}
        safe: dict[str, object] = {}
        for key, value in metadata.items():
            normalized_key = key.casefold()
            if not _SAFE_METADATA_KEY_RE.fullmatch(key) or any(
                fragment in normalized_key for fragment in _SENSITIVE_METADATA_FRAGMENTS
            ):
                raise GenerationMetadataError("metadata contains a forbidden key")
            if not isinstance(value, str | int | float | bool) and value is not None:
                raise GenerationMetadataError("metadata values must be JSON scalar values")
            if isinstance(value, str) and len(value) > 256:
                raise GenerationMetadataError("metadata string is too long")
            if isinstance(value, float) and not math.isfinite(value):
                raise GenerationMetadataError("metadata number must be finite")
            safe[key] = value
        return safe

    @staticmethod
    def _safe_session_id(session_id: str) -> str:
        digest = hashlib.sha256(session_id.encode()).hexdigest()[:12]
        return f"session-{digest}"


__all__ = [
    "ActiveGenerationConflictError",
    "GenerationGuard",
    "GenerationGuardError",
    "GenerationMetadataError",
    "GenerationNotAcceptingError",
    "GenerationSessionMismatchError",
    "GenerationState",
    "GenerationStateChanged",
    "GenerationToken",
    "InvalidGenerationTransitionError",
    "UnknownGenerationError",
]
