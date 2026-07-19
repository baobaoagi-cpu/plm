from __future__ import annotations

import hashlib
from typing import Any

import pytest
from scripts.run_minimax_spike import (
    JsonEventLogger,
    SpikeConfig,
    SpikeError,
    build_task_start,
    decode_audio,
    detect_container,
    parse_args,
    reuse_probe_ready,
    safe_provider_fields,
    split_text,
)


def make_config() -> SpikeConfig:
    return SpikeConfig(
        api_key="secret-api-key",
        model="verified-at-runtime",
        voice_id="secret-voice-id",
        output_format="mp3",
        sample_rate=24_000,
        bitrate=128_000,
        channel=1,
        speed=1.0,
        volume=1.0,
        pitch=0,
        language_boost="Chinese",
        ws_url="wss://api.minimax.io/ws/v1/t2a_v2",
        connect_timeout_s=10.0,
        receive_timeout_s=30.0,
    )


def test_config_requires_all_secret_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("MINIMAX_API_KEY", "MINIMAX_MODEL", "MINIMAX_VOICE_ID", "MINIMAX_OUTPUT_FORMAT"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(SpikeError, match="MINIMAX_API_KEY"):
        SpikeConfig.from_environment()


def test_config_rejects_non_tls_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINIMAX_API_KEY", "key")
    monkeypatch.setenv("MINIMAX_MODEL", "model")
    monkeypatch.setenv("MINIMAX_VOICE_ID", "voice")
    monkeypatch.setenv("MINIMAX_OUTPUT_FORMAT", "mp3")
    monkeypatch.setenv("MINIMAX_WS_URL", "ws://example.invalid")

    with pytest.raises(SpikeError, match="wss://"):
        SpikeConfig.from_environment()


def test_task_start_uses_runtime_values_without_exposing_them_in_repr() -> None:
    config = make_config()
    request = build_task_start(config)

    assert request["event"] == "task_start"
    assert request["model"] == "verified-at-runtime"
    assert request["voice_setting"] == {
        "voice_id": "secret-voice-id",
        "speed": 1.0,
        "vol": 1.0,
        "pitch": 0,
    }
    assert "secret-api-key" not in repr(config)
    assert "secret-voice-id" not in repr(config)
    assert config.voice_id_hash == hashlib.sha256(b"secret-voice-id").hexdigest()[:12]


def test_split_text_preserves_content_and_emits_multiple_continue_chunks() -> None:
    text = "第一段文字。第二段文字。第三段文字。"
    chunks = split_text(text, 3)

    assert len(chunks) == 3
    assert "".join(chunks) == text
    assert all(chunks)


@pytest.mark.parametrize(
    ("audio", "expected"),
    [
        (b"RIFF\x00\x00\x00\x00WAVE", "wav"),
        (b"fLaCpayload", "flac"),
        (b"ID3payload", "mp3-id3"),
        (b"\xff\xfbpayload", "mp3-frame"),
        (b"\x00\x01\x02\x03", "raw-or-continuation"),
    ],
)
def test_detect_container(audio: bytes, expected: str) -> None:
    assert detect_container(audio) == expected


def test_decode_audio_rejects_malformed_hex() -> None:
    with pytest.raises(SpikeError, match="non-hex"):
        decode_audio({"data": {"audio": "not-hex"}})


def test_safe_provider_fields_excludes_audio_and_identifiers() -> None:
    response: dict[str, Any] = {
        "session_id": "session-secret",
        "event": "task_continued",
        "trace_id": "trace-safe",
        "data": {"audio": "00ff"},
        "base_resp": {"status_code": 0, "status_msg": "success"},
    }

    fields = safe_provider_fields(response)

    assert fields["has_audio"] is True
    assert fields["trace_id"] == "trace-safe"
    assert "audio" not in fields
    assert "session_id" not in fields


def test_event_logger_includes_local_ids_without_secrets(
    capsys: pytest.CaptureFixture[str],
) -> None:
    logger = JsonEventLogger(
        voice_id_hash="voice-hash",
        probe_id="probe-standard-001",
        generation_id="generation-standard-001",
    )

    logger.emit("connected")
    output = capsys.readouterr().out

    assert '"probe_id":"probe-standard-001"' in output
    assert '"generation_id":"generation-standard-001"' in output
    assert "secret-api-key" not in output
    assert "secret-voice-id" not in output


def test_probe_and_generation_ids_are_required() -> None:
    with pytest.raises(SystemExit):
        parse_args([])

    args = parse_args(
        [
            "--probe-id",
            "probe-standard-001",
            "--generation-id",
            "generation-standard-001",
        ]
    )

    assert args.probe_id == "probe-standard-001"
    assert args.generation_id == "generation-standard-001"


def test_reuse_probe_waits_for_every_initial_continue_to_finish() -> None:
    assert reuse_probe_ready(final_count=1, expected_count=2, already_sent=False) is False
    assert reuse_probe_ready(final_count=2, expected_count=2, already_sent=False) is True
    assert reuse_probe_ready(final_count=2, expected_count=2, already_sent=True) is False


def test_reuse_probe_requires_a_second_generation_id() -> None:
    with pytest.raises(SystemExit):
        parse_args(
            [
                "--probe-id",
                "probe-reuse-001",
                "--generation-id",
                "generation-reuse-001-a",
                "--probe-reuse",
            ]
        )

    args = parse_args(
        [
            "--probe-id",
            "probe-reuse-001",
            "--generation-id",
            "generation-reuse-001-a",
            "--reuse-generation-id",
            "generation-reuse-001-b",
            "--probe-reuse",
        ]
    )

    assert args.reuse_generation_id == "generation-reuse-001-b"
