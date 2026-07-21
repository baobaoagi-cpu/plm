"""Short-lived, replay-resistant call grants for the offline protocol boundary."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SAFE_FINGERPRINT = re.compile(r"^[a-f0-9]{12,64}$")
_CLAIM_KEYS = frozenset(
    {"aud", "exp_ms", "iat_ms", "kid", "nonce", "purpose", "session_id", "sub"}
)


class CallGrantError(ValueError):
    """A safe public failure that never echoes a token or signing key."""


@dataclass(frozen=True, slots=True)
class CallGrantClaims:
    audience: str
    purpose: str
    session_id: str
    subject_fingerprint: str
    nonce: str
    key_id: str
    issued_at_ms: int
    expires_at_ms: int


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    try:
        return base64.b64decode(value + padding, altchars=b"-_", validate=True)
    except (ValueError, UnicodeEncodeError):
        raise CallGrantError("invalid call grant") from None


def _safe_id(name: str, value: str) -> str:
    if not _SAFE_ID.fullmatch(value):
        raise CallGrantError(f"{name} must be a bounded opaque identifier")
    return value


class NonceReplayGuard:
    """Bound unexpired grant nonces within one Python process.

    This offline guard is not a distributed nonce store. Callers must share one instance across
    validators in the same process; multi-worker or restart-safe single use remains unverified.
    """

    def __init__(self, *, max_entries: int = 4_096) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be positive")
        self._max_entries = max_entries
        self._lock = threading.RLock()
        self._expires_by_nonce: dict[str, int] = {}

    def consume(self, nonce: str, expires_at_ms: int, now_ms: int) -> None:
        _safe_id("nonce", nonce)
        with self._lock:
            expired = [key for key, expiry in self._expires_by_nonce.items() if expiry <= now_ms]
            for key in expired:
                del self._expires_by_nonce[key]
            if nonce in self._expires_by_nonce:
                raise CallGrantError("call grant replay rejected")
            if len(self._expires_by_nonce) >= self._max_entries:
                raise CallGrantError("call grant replay window is full")
            self._expires_by_nonce[nonce] = expires_at_ms

    @property
    def entry_count(self) -> int:
        with self._lock:
            return len(self._expires_by_nonce)


class CallGrantSigner:
    """Issue compact HMAC grants from an explicitly supplied offline key."""

    def __init__(
        self,
        key_id: str,
        signing_key: bytes,
        *,
        audience: str,
        purpose: str = "duplex_call",
        clock: Callable[[], float] = time.time,
        max_ttl_s: int = 120,
    ) -> None:
        self._key_id = _safe_id("key_id", key_id)
        if len(signing_key) < 32:
            raise ValueError("signing_key must contain at least 32 bytes")
        self._signing_key = signing_key
        self._audience = _safe_id("audience", audience)
        self._purpose = _safe_id("purpose", purpose)
        self._clock = clock
        if max_ttl_s < 1 or max_ttl_s > 300:
            raise ValueError("max_ttl_s must be between 1 and 300")
        self._max_ttl_s = max_ttl_s

    def issue(
        self,
        *,
        session_id: str,
        subject_fingerprint: str,
        nonce: str,
        ttl_s: int = 60,
    ) -> str:
        _safe_id("session_id", session_id)
        _safe_id("nonce", nonce)
        if not _SAFE_FINGERPRINT.fullmatch(subject_fingerprint):
            raise CallGrantError("subject_fingerprint must be a lowercase hex fingerprint")
        if ttl_s < 1 or ttl_s > self._max_ttl_s:
            raise CallGrantError("call grant ttl is outside the allowed bound")
        now_ms = int(self._clock() * 1_000)
        payload = {
            "aud": self._audience,
            "exp_ms": now_ms + ttl_s * 1_000,
            "iat_ms": now_ms,
            "kid": self._key_id,
            "nonce": nonce,
            "purpose": self._purpose,
            "session_id": session_id,
            "sub": subject_fingerprint,
        }
        encoded_payload = _b64url_encode(
            json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        )
        signature = hmac.new(
            self._signing_key, encoded_payload.encode("ascii"), hashlib.sha256
        ).digest()
        return f"{encoded_payload}.{_b64url_encode(signature)}"


class CallGrantValidator:
    """Verify signature, binding, time window and process-local single-use nonce."""

    def __init__(
        self,
        keys: Mapping[str, bytes],
        *,
        audience: str,
        purpose: str = "duplex_call",
        clock: Callable[[], float] = time.time,
        max_ttl_s: int = 120,
        clock_skew_s: int = 5,
        replay_guard: NonceReplayGuard | None = None,
    ) -> None:
        if not keys:
            raise ValueError("at least one verification key is required")
        self._keys = dict(keys)
        for key_id, key in self._keys.items():
            _safe_id("key_id", key_id)
            if len(key) < 32:
                raise ValueError("verification keys must contain at least 32 bytes")
        self._audience = _safe_id("audience", audience)
        self._purpose = _safe_id("purpose", purpose)
        self._clock = clock
        if max_ttl_s < 1 or max_ttl_s > 300:
            raise ValueError("max_ttl_s must be between 1 and 300")
        if clock_skew_s < 0 or clock_skew_s > 30:
            raise ValueError("clock_skew_s must be between 0 and 30")
        self._max_ttl_ms = max_ttl_s * 1_000
        self._clock_skew_ms = clock_skew_s * 1_000
        self._replay_guard = replay_guard or NonceReplayGuard()

    def verify(
        self,
        token: str,
        *,
        expected_session_id: str,
        expected_subject_fingerprint: str,
    ) -> CallGrantClaims:
        if len(token.encode("utf-8")) > 4_096 or token.count(".") != 1:
            raise CallGrantError("invalid call grant")
        encoded_payload, encoded_signature = token.split(".", maxsplit=1)
        try:
            payload = json.loads(_b64url_decode(encoded_payload))
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
            raise CallGrantError("invalid call grant") from None
        if not isinstance(payload, dict) or set(payload) != _CLAIM_KEYS:
            raise CallGrantError("invalid call grant claims")
        claims = self._claims(payload)
        key = self._keys.get(claims.key_id)
        if key is None:
            raise CallGrantError("unknown call grant key")
        expected_signature = hmac.new(
            key, encoded_payload.encode("ascii"), hashlib.sha256
        ).digest()
        signature = _b64url_decode(encoded_signature)
        if not hmac.compare_digest(signature, expected_signature):
            raise CallGrantError("invalid call grant signature")
        now_ms = int(self._clock() * 1_000)
        if claims.issued_at_ms > now_ms + self._clock_skew_ms:
            raise CallGrantError("call grant is not yet valid")
        if claims.expires_at_ms <= now_ms - self._clock_skew_ms:
            raise CallGrantError("call grant expired")
        if claims.expires_at_ms - claims.issued_at_ms > self._max_ttl_ms:
            raise CallGrantError("call grant ttl exceeds the allowed bound")
        if claims.audience != self._audience or claims.purpose != self._purpose:
            raise CallGrantError("call grant scope mismatch")
        if claims.session_id != expected_session_id:
            raise CallGrantError("call grant session mismatch")
        if claims.subject_fingerprint != expected_subject_fingerprint:
            raise CallGrantError("call grant subject mismatch")
        self._replay_guard.consume(
            claims.nonce,
            claims.expires_at_ms + self._clock_skew_ms,
            now_ms,
        )
        return claims

    @staticmethod
    def _claims(payload: dict[str, object]) -> CallGrantClaims:
        try:
            audience = _safe_id("audience", CallGrantValidator._string(payload, "aud"))
            purpose = _safe_id("purpose", CallGrantValidator._string(payload, "purpose"))
            session_id = _safe_id(
                "session_id", CallGrantValidator._string(payload, "session_id")
            )
            nonce = _safe_id("nonce", CallGrantValidator._string(payload, "nonce"))
            key_id = _safe_id("key_id", CallGrantValidator._string(payload, "kid"))
            subject = CallGrantValidator._string(payload, "sub")
            issued_value = payload["iat_ms"]
            expires_value = payload["exp_ms"]
        except (KeyError, TypeError, ValueError):
            raise CallGrantError("invalid call grant claims") from None
        if type(issued_value) is not int or type(expires_value) is not int:
            raise CallGrantError("invalid call grant time window")
        issued_at_ms = issued_value
        expires_at_ms = expires_value
        if not _SAFE_FINGERPRINT.fullmatch(subject):
            raise CallGrantError("invalid call grant subject")
        if issued_at_ms < 0 or expires_at_ms <= issued_at_ms:
            raise CallGrantError("invalid call grant time window")
        return CallGrantClaims(
            audience=audience,
            purpose=purpose,
            session_id=session_id,
            subject_fingerprint=subject,
            nonce=nonce,
            key_id=key_id,
            issued_at_ms=issued_at_ms,
            expires_at_ms=expires_at_ms,
        )

    @staticmethod
    def _string(payload: dict[str, object], key: str) -> str:
        value = payload[key]
        if not isinstance(value, str):
            raise CallGrantError("invalid call grant claims")
        return value


__all__ = [
    "CallGrantClaims",
    "CallGrantError",
    "CallGrantSigner",
    "CallGrantValidator",
    "NonceReplayGuard",
]
