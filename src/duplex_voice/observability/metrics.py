"""Allowlisted monotonic latency metrics."""

from __future__ import annotations

from dataclasses import dataclass

from duplex_voice.observability.event_log import TelemetryError

_METRICS = frozenset({"connect_ms", "first_audio_ttfa_ms", "interruption_clear_ms"})


@dataclass(frozen=True, slots=True)
class LatencySample:
    metric: str
    duration_ms: int


class LatencyTracker:
    """Measure allowlisted monotonic intervals without retaining payload data."""

    def __init__(self) -> None:
        self._starts: dict[str, int] = {}

    def start(self, metric: str, timestamp_monotonic_ms: int) -> None:
        if metric not in _METRICS:
            raise TelemetryError("latency metric is not allowlisted")
        if timestamp_monotonic_ms < 0:
            raise TelemetryError("latency timestamp must be non-negative")
        self._starts[metric] = timestamp_monotonic_ms

    def finish(self, metric: str, timestamp_monotonic_ms: int) -> LatencySample:
        if metric not in self._starts:
            raise TelemetryError("latency metric has no start marker")
        started = self._starts.pop(metric)
        if timestamp_monotonic_ms < started:
            raise TelemetryError("latency finish precedes start")
        return LatencySample(metric=metric, duration_ms=timestamp_monotonic_ms - started)


__all__ = ["LatencySample", "LatencyTracker"]
