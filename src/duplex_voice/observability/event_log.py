"""Bounded and redacted lifecycle evidence for offline resilience tests."""

from __future__ import annotations

import hashlib
import math
import re
import threading
from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

type TelemetryScalar = str | int | float | bool | None

_EVENT_NAMES = frozenset(
    {
        "call.start",
        "call.ready",
        "mic.frame.accepted",
        "generation.started",
        "first.audio",
        "playback.clear",
        "generation.finished",
        "protocol.rejected",
        "call.ended",
    }
)
_SAFE_CODE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_FORBIDDEN_KEYS = frozenset(
    {"audio", "authorization", "call_grant", "content", "prompt", "secret", "text", "transcript"}
)


class TelemetryError(ValueError):
    """Raised when an event would violate the safe telemetry contract."""


@dataclass(frozen=True, slots=True)
class SafeTelemetryEvent:
    event: str
    timestamp_monotonic_ms: int
    session_fingerprint: str
    generation_fingerprint: str | None
    attributes: Mapping[str, TelemetryScalar]


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:12]


class SafeTelemetryBuffer:
    """Retain only a bounded redacted event tail."""

    def __init__(self, *, max_events: int = 256) -> None:
        if max_events < 1 or max_events > 10_000:
            raise ValueError("max_events must be between 1 and 10000")
        self._events: deque[SafeTelemetryEvent] = deque(maxlen=max_events)
        self._lock = threading.RLock()
        self._total_recorded = 0

    def record(
        self,
        event: str,
        *,
        timestamp_monotonic_ms: int,
        session_id: str,
        generation_id: str | None = None,
        attributes: Mapping[str, TelemetryScalar] | None = None,
    ) -> SafeTelemetryEvent:
        if event not in _EVENT_NAMES:
            raise TelemetryError("telemetry event is not allowlisted")
        if timestamp_monotonic_ms < 0:
            raise TelemetryError("telemetry timestamp must be non-negative")
        safe_attributes = self._sanitize_attributes(attributes or {})
        item = SafeTelemetryEvent(
            event=event,
            timestamp_monotonic_ms=timestamp_monotonic_ms,
            session_fingerprint=_fingerprint(session_id),
            generation_fingerprint=(
                _fingerprint(generation_id) if generation_id is not None else None
            ),
            attributes=MappingProxyType(safe_attributes),
        )
        with self._lock:
            self._events.append(item)
            self._total_recorded += 1
        return item

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "total_recorded": self._total_recorded,
                "retained_events": len(self._events),
                "events": tuple(self._events),
            }

    @staticmethod
    def _sanitize_attributes(
        attributes: Mapping[str, TelemetryScalar],
    ) -> dict[str, TelemetryScalar]:
        if len(attributes) > 8:
            raise TelemetryError("too many telemetry attributes")
        safe: dict[str, TelemetryScalar] = {}
        for key, value in attributes.items():
            normalized = key.casefold()
            if not _SAFE_CODE.fullmatch(key) or any(part in normalized for part in _FORBIDDEN_KEYS):
                raise TelemetryError("telemetry attribute key is forbidden")
            if isinstance(value, str) and not _SAFE_CODE.fullmatch(value):
                raise TelemetryError("telemetry strings must be safe machine codes")
            if isinstance(value, float) and not math.isfinite(value):
                raise TelemetryError("telemetry numbers must be finite")
            safe[key] = value
        return safe


__all__ = ["SafeTelemetryBuffer", "SafeTelemetryEvent", "TelemetryError", "TelemetryScalar"]
