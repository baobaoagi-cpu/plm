from __future__ import annotations

import json

import pytest

from duplex_voice.api.call_grant import CallGrantSigner, CallGrantValidator
from duplex_voice.api.ingress import ProtocolIngressError, ProtocolSessionGate

KEY = bytes(range(32))
SUBJECT = "a" * 32


def _token(session_id: str, nonce: str = "nonce-1") -> str:
    return CallGrantSigner(
        "key-1", KEY, audience="xiewenxian-offline", clock=lambda: 1_000.0
    ).issue(
        session_id=session_id,
        subject_fingerprint=SUBJECT,
        nonce=nonce,
    )


def _gate(session_id: str = "session-1", *, message_window: int = 32) -> ProtocolSessionGate:
    return ProtocolSessionGate(
        session_id,
        SUBJECT,
        CallGrantValidator(
            {"key-1": KEY}, audience="xiewenxian-offline", clock=lambda: 1_000.0
        ),
        message_window=message_window,
    )


def _frame(
    event_type: str,
    sequence: int,
    payload: dict[str, object],
    *,
    session_id: str = "session-1",
    message_id: str | None = None,
    generation_id: str | None = None,
) -> str:
    return json.dumps(
        {
            "protocol_version": "1",
            "type": event_type,
            "session_id": session_id,
            "message_id": message_id or f"message-{sequence}",
            "sequence": sequence,
            "generation_id": generation_id,
            "payload": payload,
        }
    )


def _start(gate: ProtocolSessionGate, *, token: str | None = None) -> None:
    decision = gate.accept(
        _frame("call.start", 1, {"call_grant": token or _token("session-1")})
    )
    assert decision.accepted_sequence == 1
    assert len(decision.session_fingerprint) == 12


def test_call_start_must_be_first_and_grant_must_be_valid() -> None:
    gate = _gate()
    with pytest.raises(ProtocolIngressError, match="first"):
        gate.accept(_frame("heartbeat", 1, {"sent_at_monotonic_ms": 1}))

    with pytest.raises(ProtocolIngressError, match="grant") as exc_info:
        gate.accept(_frame("call.start", 1, {"call_grant": "sensitive-invalid-grant"}))
    assert "sensitive-invalid-grant" not in str(exc_info.value)


def test_duplicate_out_of_order_and_session_mismatch_do_not_advance_state() -> None:
    gate = _gate()
    start = _frame("call.start", 1, {"call_grant": _token("session-1")})
    gate.accept(start)
    with pytest.raises(ProtocolIngressError, match="duplicate"):
        gate.accept(start)
    with pytest.raises(ProtocolIngressError, match="contiguous"):
        gate.accept(_frame("heartbeat", 3, {"sent_at_monotonic_ms": 3}))
    with pytest.raises(ProtocolIngressError, match="session"):
        gate.accept(
            _frame(
                "heartbeat",
                2,
                {"sent_at_monotonic_ms": 2},
                session_id="session-other",
            )
        )

    assert gate.accept(_frame("heartbeat", 2, {"sent_at_monotonic_ms": 2})).accepted_sequence == 2


def test_audio_frames_require_exact_20ms_payload_and_monotonic_timestamp() -> None:
    gate = _gate()
    _start(gate)
    valid_payload = {
        "timestamp_monotonic_ms": 20,
        "encoding": "pcm_s16le",
        "sample_rate": 16000,
        "channels": 1,
        "frame_duration_ms": 20,
        "payload_length": 640,
    }
    gate.accept(_frame("audio.input", 2, valid_payload))

    wrong_size = {**valid_payload, "timestamp_monotonic_ms": 40, "payload_length": 320}
    with pytest.raises(ProtocolIngressError, match="length"):
        gate.accept(_frame("audio.input", 3, wrong_size))
    repeated_time = {**valid_payload, "timestamp_monotonic_ms": 20}
    with pytest.raises(ProtocolIngressError, match="timestamps"):
        gate.accept(_frame("audio.input", 3, repeated_time))
    next_frame = {**valid_payload, "timestamp_monotonic_ms": 40}
    assert gate.accept(_frame("audio.input", 3, next_frame)).accepted_sequence == 3


def test_stale_generation_frames_are_rejected_without_consuming_sequence() -> None:
    gate = _gate()
    _start(gate)
    gate.activate_generation("generation-1")
    gate.accept(
        _frame(
            "generation.interrupt",
            2,
            {"reason": "user_interruption"},
            generation_id="generation-1",
        )
    )
    assert gate.clear_generation("generation-1")
    gate.activate_generation("generation-2")
    with pytest.raises(ProtocolIngressError, match="stale"):
        gate.accept(
            _frame(
                "playback.drained",
                3,
                {"last_audio_sequence": 10},
                generation_id="generation-1",
            )
        )
    assert (
        gate.accept(
            _frame(
                "playback.drained",
                3,
                {"last_audio_sequence": 10},
                generation_id="generation-2",
            )
        ).accepted_sequence
        == 3
    )


def test_hangup_is_terminal_and_repeated_call_start_is_rejected() -> None:
    gate = _gate()
    _start(gate)
    with pytest.raises(ProtocolIngressError, match="repeated"):
        gate.accept(_frame("call.start", 2, {"call_grant": _token("session-1", "nonce-2")}))
    gate.accept(_frame("call.end", 2, {"reason": "user_hangup"}))
    with pytest.raises(ProtocolIngressError, match="ended"):
        gate.accept(_frame("heartbeat", 3, {"sent_at_monotonic_ms": 3}))


@pytest.mark.parametrize(
    "raw",
    [
        b"\xff\xfe",
        "x" * 70_000,
        json.dumps({"type": "unknown"}),
        json.dumps({"protocol_version": "1", "type": "call.start", "secret": "do-not-echo"}),
    ],
    ids=["invalid-utf8", "oversized", "unknown-type", "sensitive-extra"],
)
def test_chaos_frames_fail_safely_without_echo(raw: str | bytes) -> None:
    gate = _gate()
    with pytest.raises(ProtocolIngressError) as exc_info:
        gate.accept(raw)
    assert "do-not-echo" not in str(exc_info.value)


def test_ten_thousand_ordered_frames_keep_replay_memory_bounded() -> None:
    gate = _gate(message_window=64)
    _start(gate)
    for sequence in range(2, 10_001):
        gate.accept(
            _frame(
                "heartbeat",
                sequence,
                {"sent_at_monotonic_ms": sequence},
            )
        )

    assert gate.last_sequence == 10_000
    assert gate.retained_message_ids == 64


def test_one_thousand_reconnects_require_fresh_session_bound_grants() -> None:
    validator = CallGrantValidator(
        {"key-1": KEY}, audience="xiewenxian-offline", clock=lambda: 1_000.0
    )
    for index in range(1_000):
        session_id = f"reconnect-{index}"
        gate = ProtocolSessionGate(session_id, SUBJECT, validator, message_window=8)
        token = _token(session_id, nonce=f"reconnect-nonce-{index}")
        assert (
            gate.accept(
                _frame(
                    "call.start",
                    1,
                    {"call_grant": token},
                    session_id=session_id,
                )
            ).accepted_sequence
            == 1
        )
        assert (
            gate.accept(
                _frame(
                    "call.end",
                    2,
                    {"reason": "synthetic_reconnect"},
                    session_id=session_id,
                )
            ).accepted_sequence
            == 2
        )
