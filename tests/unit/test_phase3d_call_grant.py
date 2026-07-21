from __future__ import annotations

import base64
import hashlib
import hmac
import json

import pytest

from duplex_voice.api.call_grant import (
    CallGrantError,
    CallGrantSigner,
    CallGrantValidator,
    NonceReplayGuard,
)

KEY_ONE = bytes(range(32))
KEY_TWO = bytes(range(1, 33))
SUBJECT = "a" * 32


def _grant(clock: list[float], *, key_id: str = "key-1", key: bytes = KEY_ONE) -> str:
    return CallGrantSigner(
        key_id,
        key,
        audience="xiewenxian-offline",
        clock=lambda: clock[0],
    ).issue(
        session_id="session-1",
        subject_fingerprint=SUBJECT,
        nonce="nonce-1",
        ttl_s=60,
    )


def _validator(
    clock: list[float],
    *,
    keys: dict[str, bytes] | None = None,
    replay_guard: NonceReplayGuard | None = None,
) -> CallGrantValidator:
    return CallGrantValidator(
        keys or {"key-1": KEY_ONE},
        audience="xiewenxian-offline",
        clock=lambda: clock[0],
        replay_guard=replay_guard,
    )


def test_short_lived_grant_binds_session_subject_audience_and_purpose() -> None:
    clock = [1_000.0]
    claims = _validator(clock).verify(
        _grant(clock),
        expected_session_id="session-1",
        expected_subject_fingerprint=SUBJECT,
    )

    assert claims.session_id == "session-1"
    assert claims.subject_fingerprint == SUBJECT
    assert claims.audience == "xiewenxian-offline"
    assert claims.purpose == "duplex_call"
    assert claims.expires_at_ms - claims.issued_at_ms == 60_000


def test_grant_is_single_use_across_connections() -> None:
    clock = [1_000.0]
    validator = _validator(clock)
    token = _grant(clock)
    validator.verify(
        token,
        expected_session_id="session-1",
        expected_subject_fingerprint=SUBJECT,
    )

    with pytest.raises(CallGrantError, match="replay"):
        validator.verify(
            token,
            expected_session_id="session-1",
            expected_subject_fingerprint=SUBJECT,
        )


def test_replay_nonce_remains_consumed_through_clock_skew_window() -> None:
    clock = [1_000.0]
    validator = _validator(clock)
    token = _grant(clock)
    validator.verify(
        token,
        expected_session_id="session-1",
        expected_subject_fingerprint=SUBJECT,
    )
    clock[0] = 1_062.0

    with pytest.raises(CallGrantError, match="replay"):
        validator.verify(
            token,
            expected_session_id="session-1",
            expected_subject_fingerprint=SUBJECT,
        )


@pytest.mark.parametrize(
    ("session_id", "subject", "error"),
    [
        ("session-other", SUBJECT, "session"),
        ("session-1", "b" * 32, "subject"),
    ],
)
def test_grant_rejects_binding_mismatch(
    session_id: str, subject: str, error: str
) -> None:
    clock = [1_000.0]

    with pytest.raises(CallGrantError, match=error):
        _validator(clock).verify(
            _grant(clock),
            expected_session_id=session_id,
            expected_subject_fingerprint=subject,
        )


def test_expired_and_future_grants_fail_closed() -> None:
    clock = [1_000.0]
    token = _grant(clock)
    clock[0] = 1_066.0
    with pytest.raises(CallGrantError, match="expired"):
        _validator(clock).verify(
            token,
            expected_session_id="session-1",
            expected_subject_fingerprint=SUBJECT,
        )

    clock[0] = 900.0
    with pytest.raises(CallGrantError, match="not yet valid"):
        _validator(clock).verify(
            token,
            expected_session_id="session-1",
            expected_subject_fingerprint=SUBJECT,
        )


def test_tampering_never_echoes_the_token() -> None:
    clock = [1_000.0]
    token = _grant(clock)
    payload, signature = token.split(".")
    tampered = f"{payload[:-1]}A.{signature}"

    with pytest.raises(CallGrantError) as exc_info:
        _validator(clock).verify(
            tampered,
            expected_session_id="session-1",
            expected_subject_fingerprint=SUBJECT,
        )

    assert tampered not in str(exc_info.value)
    assert token not in str(exc_info.value)


def test_key_rotation_accepts_active_keys_and_rejects_unknown_key() -> None:
    clock = [1_000.0]
    rotated = _grant(clock, key_id="key-2", key=KEY_TWO)
    validator = _validator(clock, keys={"key-1": KEY_ONE, "key-2": KEY_TWO})

    assert (
        validator.verify(
            rotated,
            expected_session_id="session-1",
            expected_subject_fingerprint=SUBJECT,
        ).key_id
        == "key-2"
    )

    with pytest.raises(CallGrantError, match="unknown"):
        _validator(clock).verify(
            rotated,
            expected_session_id="session-1",
            expected_subject_fingerprint=SUBJECT,
        )


def test_oversized_ttl_is_rejected_by_issuer_and_validator() -> None:
    clock = [1_000.0]
    signer = CallGrantSigner(
        "key-1", KEY_ONE, audience="xiewenxian-offline", clock=lambda: clock[0]
    )
    with pytest.raises(CallGrantError, match="ttl"):
        signer.issue(
            session_id="session-1",
            subject_fingerprint=SUBJECT,
            nonce="nonce-long",
            ttl_s=121,
        )

    token = _grant(clock)
    encoded_payload, signature = token.split(".")
    payload = json.loads(
        base64.urlsafe_b64decode(encoded_payload + "=" * (-len(encoded_payload) % 4))
    )
    payload["exp_ms"] = payload["iat_ms"] + 121_000
    altered_payload = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    ).rstrip(b"=").decode()
    forged = f"{altered_payload}.{signature}"
    with pytest.raises(CallGrantError):
        _validator(clock).verify(
            forged,
            expected_session_id="session-1",
            expected_subject_fingerprint=SUBJECT,
        )


def test_replay_guard_is_bounded_and_recovers_after_expiry() -> None:
    guard = NonceReplayGuard(max_entries=2)
    guard.consume("nonce-1", 2_000, 1_000)
    guard.consume("nonce-2", 2_000, 1_000)
    with pytest.raises(CallGrantError, match="full"):
        guard.consume("nonce-3", 3_000, 1_000)

    guard.consume("nonce-3", 3_000, 2_000)
    assert guard.entry_count == 1


def test_non_string_scope_claim_is_rejected_even_with_valid_signature() -> None:
    clock = [1_000.0]
    signer = CallGrantSigner(
        "key-1", KEY_ONE, audience="xiewenxian-offline", clock=lambda: clock[0]
    )
    token = signer.issue(
        session_id="session-1",
        subject_fingerprint=SUBJECT,
        nonce="nonce-strict",
    )
    encoded_payload, _signature = token.split(".")
    payload = json.loads(
        base64.urlsafe_b64decode(encoded_payload + "=" * (-len(encoded_payload) % 4))
    )
    payload["purpose"] = 123
    altered_payload = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    ).rstrip(b"=").decode()
    signature = base64.urlsafe_b64encode(
        hmac.new(KEY_ONE, altered_payload.encode("ascii"), hashlib.sha256).digest()
    ).rstrip(b"=").decode()
    with pytest.raises(CallGrantError, match="claims"):
        _validator(clock).verify(
            f"{altered_payload}.{signature}",
            expected_session_id="session-1",
            expected_subject_fingerprint=SUBJECT,
        )
