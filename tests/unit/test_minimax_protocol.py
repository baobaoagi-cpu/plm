from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from duplex_voice.tts.minimax_protocol import (
    MiniMaxAudioEvent,
    MiniMaxAudioPayloadError,
    MiniMaxAudioSettings,
    MiniMaxConfigurationError,
    MiniMaxConnectedSuccess,
    MiniMaxMalformedEventError,
    MiniMaxProviderError,
    MiniMaxSocketClosed,
    MiniMaxTaskContinue,
    MiniMaxTaskContinued,
    MiniMaxTaskFinish,
    MiniMaxTaskFinished,
    MiniMaxTaskStart,
    MiniMaxTaskStarted,
    MiniMaxUnknownEvent,
    MiniMaxUnsupportedReuseError,
    MiniMaxVoiceSettings,
    decode_audio_payload,
    parse_minimax_event,
    redact_mapping,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "minimax_events"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def task_start() -> MiniMaxTaskStart:
    return MiniMaxTaskStart(
        model="speech-verified-fixture",
        voice=MiniMaxVoiceSettings("private-voice-id"),
        audio=MiniMaxAudioSettings(24_000, 128_000, "mp3", 1),
        language_boost="Chinese",
    )


def test_outbound_task_start_serializes_verified_shape() -> None:
    assert task_start().to_payload() == {
        "event": "task_start",
        "model": "speech-verified-fixture",
        "voice_setting": {
            "voice_id": "private-voice-id",
            "speed": 1.0,
            "vol": 1.0,
            "pitch": 0,
        },
        "audio_setting": {
            "sample_rate": 24_000,
            "bitrate": 128_000,
            "format": "mp3",
            "channel": 1,
        },
        "language_boost": "Chinese",
    }


def test_outbound_task_continue_and_finish_serialize_verified_shapes() -> None:
    assert MiniMaxTaskContinue("short private text").to_payload() == {
        "event": "task_continue",
        "text": "short private text",
    }
    assert MiniMaxTaskFinish().to_payload() == {"event": "task_finish"}


@pytest.mark.parametrize(
    "constructor",
    [
        lambda: MiniMaxVoiceSettings(""),
        lambda: MiniMaxAudioSettings(0, 128_000, "mp3", 1),
        lambda: MiniMaxTaskContinue("  "),
        lambda: MiniMaxTaskStart(
            "", MiniMaxVoiceSettings("voice"), MiniMaxAudioSettings(1, 1, "mp3", 1)
        ),
    ],
)
def test_outbound_models_reject_missing_required_values(constructor: Callable[[], object]) -> None:
    with pytest.raises(MiniMaxConfigurationError):
        constructor()


def test_secret_outbound_fields_are_absent_from_repr() -> None:
    start = task_start()
    continued = MiniMaxTaskContinue("private synthesis text")

    assert "private-voice-id" not in repr(start)
    assert "private synthesis text" not in repr(continued)
    assert start.voice.voice_id_hash


def test_parse_connected_success() -> None:
    event = parse_minimax_event(fixture("connected_success.json"))
    assert isinstance(event, MiniMaxConnectedSuccess)
    assert event.status.status_code == 0
    assert event.trace_id == "fixture-trace-connected"
    assert "synthetic success" not in repr(event)


def test_parse_task_started_from_utf8_bytes() -> None:
    event = parse_minimax_event(fixture("task_started.json").encode())
    assert isinstance(event, MiniMaxTaskStarted)


def test_parse_audio_event_and_verified_metadata() -> None:
    event = parse_minimax_event(fixture("audio_event.json"))
    assert isinstance(event, MiniMaxAudioEvent)
    assert event.audio == b"ID3\x00"
    assert event.audio_bytes == 4
    assert event.metadata.audio_format == "mp3"
    assert event.metadata.sample_rate == 24_000
    assert event.metadata.channel_count == 1
    assert "49443300" not in repr(event)


def test_decode_audio_payload_returns_bytes_and_hash_is_metadata_only() -> None:
    event = parse_minimax_event(fixture("audio_event.json"))
    assert isinstance(event, MiniMaxAudioEvent)
    assert decode_audio_payload("00ff") == b"\x00\xff"
    assert len(event.audio_sha256) == 64


def test_parse_final_task_continued_without_audio() -> None:
    event = parse_minimax_event(fixture("task_continued_final.json"))
    assert isinstance(event, MiniMaxTaskContinued)
    assert event.is_final is True


def test_parse_task_finished_and_metadata() -> None:
    event = parse_minimax_event(fixture("task_finished.json"))
    assert isinstance(event, MiniMaxTaskFinished)
    assert event.metadata.audio_length_ms == 1439


def test_status_2206_maps_to_explicit_unsupported_reuse_error() -> None:
    with pytest.raises(MiniMaxUnsupportedReuseError) as raised:
        parse_minimax_event(fixture("provider_error_2206.json"))
    assert raised.value.event.status.status_code == 2206
    assert "synthetic reuse rejection" not in str(raised.value)


def test_other_provider_error_uses_safe_provider_exception() -> None:
    raw = json.dumps(
        {
            "event": "task_failed",
            "base_resp": {"status_code": 9999, "status_msg": "private provider message"},
        }
    )
    with pytest.raises(MiniMaxProviderError) as raised:
        parse_minimax_event(raw)
    assert "private provider message" not in str(raised.value)


@pytest.mark.parametrize("raw", ["{", "[]", b"\xff", '{"event":"task_started"}'])
def test_malformed_known_events_raise_typed_error(raw: str | bytes) -> None:
    with pytest.raises(MiniMaxMalformedEventError):
        parse_minimax_event(raw)


@pytest.mark.parametrize("payload", [None, "", "not-hex", 123])
def test_invalid_audio_payload_raises_typed_error(payload: object) -> None:
    with pytest.raises(MiniMaxAudioPayloadError):
        decode_audio_payload(payload)


def test_parser_rejects_invalid_audio_payload() -> None:
    raw = json.dumps(
        {
            "event": "task_continued",
            "data": {"audio": "not-hex"},
            "base_resp": {"status_code": 0},
        }
    )
    with pytest.raises(MiniMaxAudioPayloadError):
        parse_minimax_event(raw)


def test_unknown_event_returns_typed_sanitized_fallback() -> None:
    event = parse_minimax_event(fixture("unknown_event.json"))
    assert isinstance(event, MiniMaxUnknownEvent)
    representation = repr(event)
    assert event.provider_event == "future_provider_event"
    assert "synthetic-sensitive-voice" not in representation
    assert "synthetic private content" not in representation


def test_missing_event_type_returns_unknown_instead_of_crashing() -> None:
    event = parse_minimax_event('{"trace_id":"fixture-no-event","unexpected":true}')
    assert isinstance(event, MiniMaxUnknownEvent)
    assert event.provider_event is None


def test_unknown_extra_fields_do_not_break_known_event() -> None:
    payload = json.loads(fixture("connected_success.json"))
    payload["future_field"] = {"nested": True}
    event = parse_minimax_event(json.dumps(payload))
    assert isinstance(event, MiniMaxConnectedSuccess)


def test_redaction_removes_api_key_authorization_voice_text_and_audio() -> None:
    safe = redact_mapping(
        {
            "api_key": "private-api-key",
            "Authorization": "Bearer private-api-key",
            "voice_id": "private-voice-id",
            "text": "private text",
            "data": {"audio": "49443300"},
        }
    )
    representation = repr(safe)
    for secret in (
        "private-api-key",
        "Bearer private-api-key",
        "private-voice-id",
        "private text",
        "49443300",
    ):
        assert secret not in representation


def test_socket_close_reason_is_hashed_not_retained() -> None:
    event = MiniMaxSocketClosed.from_transport(1000, "private close reason")
    assert event.code == 1000
    assert event.reason_chars == 20
    assert "private close reason" not in repr(event)


def test_fixtures_are_synthetic_and_contain_no_credential_fields() -> None:
    fixture_text = "\n".join(path.read_text(encoding="utf-8") for path in FIXTURES.glob("*.json"))
    lowered = fixture_text.lower()
    assert "api_key" not in lowered
    assert "authorization" not in lowered
    assert "bearer " not in lowered
    assert "10f2bc0e06ba" not in lowered
