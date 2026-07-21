from __future__ import annotations

import pytest

from duplex_voice.audio.duplex_simulator import OfflineDuplexHarness
from duplex_voice.observability import LatencyTracker, SafeTelemetryBuffer, TelemetryError


def test_telemetry_hashes_ids_and_rejects_sensitive_attributes() -> None:
    telemetry = SafeTelemetryBuffer(max_events=4)
    event = telemetry.record(
        "generation.started",
        timestamp_monotonic_ms=10,
        session_id="session-secret-identifier",
        generation_id="generation-secret-identifier",
        attributes={"transport": "offline"},
    )

    assert "session-secret-identifier" not in repr(event)
    assert "generation-secret-identifier" not in repr(event)
    assert len(event.session_fingerprint) == 12
    with pytest.raises(TelemetryError, match="forbidden"):
        telemetry.record(
            "first.audio",
            timestamp_monotonic_ms=20,
            session_id="session-1",
            attributes={"transcript": "sensitive words"},
        )


def test_latency_tracker_records_only_allowlisted_monotonic_durations() -> None:
    tracker = LatencyTracker()
    tracker.start("first_audio_ttfa_ms", 100)
    assert tracker.finish("first_audio_ttfa_ms", 245).duration_ms == 145
    with pytest.raises(TelemetryError, match="allowlisted"):
        tracker.start("provider_billing_ms", 0)
    tracker.start("connect_ms", 100)
    with pytest.raises(TelemetryError, match="precedes"):
        tracker.finish("connect_ms", 99)


def test_ten_thousand_events_retain_only_bounded_safe_tail() -> None:
    telemetry = SafeTelemetryBuffer(max_events=128)
    for index in range(10_000):
        telemetry.record(
            "mic.frame.accepted",
            timestamp_monotonic_ms=index * 20,
            session_id="session-1",
            attributes={"sequence": index + 1},
        )

    snapshot = telemetry.snapshot()
    assert snapshot["total_recorded"] == 10_000
    assert snapshot["retained_events"] == 128
    events = snapshot["events"]
    assert isinstance(events, tuple)
    assert len(events) == 128


def test_one_thousand_generations_never_play_stale_audio_and_cleanup_is_bounded() -> None:
    harness = OfflineDuplexHarness("session-soak", output_max_pending_ms=100)
    for _cycle in range(1_000):
        token = harness.start_generation()
        assert harness.receive_assistant_audio(
            token, sequence=1, payload=b"synthetic", duration_ms=20
        )
        harness.interrupt(token)
        assert not harness.receive_assistant_audio(
            token, sequence=2, payload=b"late", duration_ms=20
        )
        assert harness.play_next() is None
        harness.guard.cleanup(cutoff_monotonic=1_000_000_000_000.0)

    assert harness.guard.record_count == 0
    assert harness.output_queue.stats().played_items == 0
    assert harness.output_queue.stats().stale_items_dropped == 1_000
