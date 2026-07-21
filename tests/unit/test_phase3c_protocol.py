from __future__ import annotations

import json

import pytest

from duplex_voice.api.protocol import (
    AudioInputFrame,
    CallEndFrame,
    CallStartFrame,
    GenerationInterruptFrame,
    HeartbeatFrame,
    PlaybackDrainedFrame,
    ProtocolViolation,
    parse_client_frame,
)


def _envelope(event_type: str, payload: dict[str, object]) -> dict[str, object]:
    return {
        "protocol_version": "1",
        "type": event_type,
        "session_id": "session-1",
        "message_id": "message-1",
        "sequence": 1,
        "generation_id": None,
        "payload": payload,
    }


@pytest.mark.parametrize(
    ("frame", "expected_type"),
    [
        (
            _envelope("call.start", {"call_grant": "synthetic-grant"}),
            CallStartFrame,
        ),
        (
            _envelope(
                "audio.input",
                {
                    "timestamp_monotonic_ms": 100,
                    "encoding": "pcm_s16le",
                    "sample_rate": 16000,
                    "channels": 1,
                    "frame_duration_ms": 20,
                    "payload_length": 640,
                },
            ),
            AudioInputFrame,
        ),
        (
            {
                **_envelope("generation.interrupt", {"reason": "user_interruption"}),
                "generation_id": "generation-1",
            },
            GenerationInterruptFrame,
        ),
        (
            {
                **_envelope("playback.drained", {"last_audio_sequence": 3}),
                "generation_id": "generation-1",
            },
            PlaybackDrainedFrame,
        ),
        (_envelope("call.end", {"reason": "user_hangup"}), CallEndFrame),
        (
            _envelope("heartbeat", {"sent_at_monotonic_ms": 500}),
            HeartbeatFrame,
        ),
    ],
)
def test_every_client_frame_has_a_strict_typed_contract(
    frame: dict[str, object], expected_type: type[object]
) -> None:
    parsed = parse_client_frame(json.dumps(frame))

    assert isinstance(parsed, expected_type)


@pytest.mark.parametrize(
    "mutation",
    [
        {"protocol_version": "2"},
        {"type": "unknown.event"},
        {"sequence": 0},
        {"generation_id": "client-invented-generation"},
        {"external_user_id": "U-untrusted"},
    ],
)
def test_call_start_rejects_unknown_version_type_identity_and_extra_fields(
    mutation: dict[str, object],
) -> None:
    frame = _envelope("call.start", {"call_grant": "secret-value"})
    frame.update(mutation)

    with pytest.raises(ProtocolViolation, match="invalid protocol") as exc_info:
        parse_client_frame(json.dumps(frame))

    assert "secret-value" not in str(exc_info.value)
    assert "U-untrusted" not in str(exc_info.value)


def test_call_grant_is_masked_in_model_representation() -> None:
    parsed = parse_client_frame(
        json.dumps(_envelope("call.start", {"call_grant": "secret-value"}))
    )

    assert isinstance(parsed, CallStartFrame)
    assert "secret-value" not in repr(parsed)


def test_frame_size_is_enforced_before_json_validation() -> None:
    with pytest.raises(ProtocolViolation, match="size limit"):
        parse_client_frame("x" * 1_025, max_frame_bytes=1_024)


def test_invalid_utf8_is_rejected_without_echo() -> None:
    with pytest.raises(ProtocolViolation, match="invalid protocol"):
        parse_client_frame(b"\xff\xfe")


def test_audio_contract_rejects_non_mono_or_wrong_sample_rate() -> None:
    frame = _envelope(
        "audio.input",
        {
            "timestamp_monotonic_ms": 100,
            "encoding": "pcm_s16le",
            "sample_rate": 48000,
            "channels": 2,
            "frame_duration_ms": 20,
            "payload_length": 640,
        },
    )

    with pytest.raises(ProtocolViolation):
        parse_client_frame(json.dumps(frame))
