"""Typed, side-effect-free models for the verified MiniMax WebSocket protocol.

This module deliberately owns no socket, retry, playback, Pipecat, or LiveKit behavior.
Unknown provider events remain typed data instead of extending the verified schema by guesswork.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Literal

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]


class MiniMaxProtocolError(RuntimeError):
    """Base class for safe MiniMax protocol failures."""


class MiniMaxMalformedEventError(MiniMaxProtocolError):
    """Raised when a known provider event is not valid JSON or has an invalid shape."""


class MiniMaxAuthenticationError(MiniMaxProtocolError):
    """Reserved for a verified authentication failure mapping."""


class MiniMaxConfigurationError(MiniMaxProtocolError):
    """Raised when an outbound event cannot be constructed safely."""


class MiniMaxProviderError(MiniMaxProtocolError):
    """Raised for a provider-declared failure without exposing its raw message."""

    def __init__(self, event: MiniMaxProviderErrorEvent) -> None:
        self.event = event
        super().__init__(
            f"MiniMax provider error event={event.event_type!r} "
            f"status={event.status.status_code!r} "
            f"message_sha256={event.status.message_sha256!r}"
        )


class MiniMaxTaskStateError(MiniMaxProviderError):
    """Raised when the provider rejects the current task/session state."""


class MiniMaxUnsupportedReuseError(MiniMaxTaskStateError):
    """Raised for verified status 2206 when attempting same-session reuse."""


class MiniMaxAudioPayloadError(MiniMaxMalformedEventError):
    """Raised when the verified hex audio payload cannot be decoded."""


@dataclass(frozen=True, slots=True)
class MiniMaxVoiceSettings:
    """Voice controls used by ``task_start``; the Voice ID is never represented."""

    voice_id: str = field(repr=False)
    speed: float = 1.0
    volume: float = 1.0
    pitch: int = 0

    def __post_init__(self) -> None:
        if not self.voice_id.strip():
            raise MiniMaxConfigurationError("voice_id must not be empty")

    @property
    def voice_id_hash(self) -> str:
        return _short_hash(self.voice_id)

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "voice_id": self.voice_id,
            "speed": self.speed,
            "vol": self.volume,
            "pitch": self.pitch,
        }


@dataclass(frozen=True, slots=True)
class MiniMaxAudioSettings:
    """Requested output settings for ``task_start``."""

    sample_rate: int
    bitrate: int
    format: str
    channel: int

    def __post_init__(self) -> None:
        if self.sample_rate <= 0 or self.bitrate <= 0 or self.channel <= 0:
            raise MiniMaxConfigurationError("audio numeric settings must be positive")
        if not self.format.strip():
            raise MiniMaxConfigurationError("audio format must not be empty")

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "sample_rate": self.sample_rate,
            "bitrate": self.bitrate,
            "format": self.format,
            "channel": self.channel,
        }


@dataclass(frozen=True, slots=True)
class MiniMaxTaskStart:
    model: str
    voice: MiniMaxVoiceSettings
    audio: MiniMaxAudioSettings
    language_boost: str | None = None
    event: Literal["task_start"] = field(default="task_start", init=False)

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise MiniMaxConfigurationError("model must not be empty")

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "event": self.event,
            "model": self.model,
            "voice_setting": self.voice.to_payload(),
            "audio_setting": self.audio.to_payload(),
        }
        if self.language_boost is not None:
            payload["language_boost"] = self.language_boost
        return payload


@dataclass(frozen=True, slots=True)
class MiniMaxTaskContinue:
    text: str = field(repr=False)
    event: Literal["task_continue"] = field(default="task_continue", init=False)

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise MiniMaxConfigurationError("task_continue text must not be empty")

    def to_payload(self) -> dict[str, JsonValue]:
        return {"event": self.event, "text": self.text}


@dataclass(frozen=True, slots=True)
class MiniMaxTaskFinish:
    event: Literal["task_finish"] = field(default="task_finish", init=False)

    def to_payload(self) -> dict[str, JsonValue]:
        return {"event": self.event}


type MiniMaxOutboundEvent = MiniMaxTaskStart | MiniMaxTaskContinue | MiniMaxTaskFinish


@dataclass(frozen=True, slots=True)
class MiniMaxBaseResponse:
    status_code: int
    message_sha256: str | None = None
    message_chars: int | None = None


@dataclass(frozen=True, slots=True)
class MiniMaxProviderMetadata:
    audio_format: str | None = None
    sample_rate: int | None = None
    channel_count: int | None = None
    audio_length_ms: int | None = None


@dataclass(frozen=True, slots=True)
class MiniMaxConnectedSuccess:
    status: MiniMaxBaseResponse
    trace_id: str | None = None
    request_id: str | None = None
    event_type: Literal["connected_success"] = field(default="connected_success", init=False)


@dataclass(frozen=True, slots=True)
class MiniMaxTaskStarted:
    status: MiniMaxBaseResponse
    trace_id: str | None = None
    request_id: str | None = None
    event_type: Literal["task_started"] = field(default="task_started", init=False)


@dataclass(frozen=True, slots=True)
class MiniMaxTaskContinued:
    status: MiniMaxBaseResponse
    is_final: bool | None
    trace_id: str | None = None
    request_id: str | None = None
    event_type: Literal["task_continued"] = field(default="task_continued", init=False)


@dataclass(frozen=True, slots=True)
class MiniMaxAudioEvent:
    provider_event: str
    audio: bytes = field(repr=False)
    status: MiniMaxBaseResponse = field(default_factory=lambda: MiniMaxBaseResponse(0))
    is_final: bool | None = None
    trace_id: str | None = None
    request_id: str | None = None
    metadata: MiniMaxProviderMetadata = field(default_factory=MiniMaxProviderMetadata)
    event_type: Literal["audio"] = field(default="audio", init=False)

    @property
    def audio_bytes(self) -> int:
        return len(self.audio)

    @property
    def audio_sha256(self) -> str:
        return hashlib.sha256(self.audio).hexdigest()


@dataclass(frozen=True, slots=True)
class MiniMaxTaskFinished:
    status: MiniMaxBaseResponse
    trace_id: str | None = None
    request_id: str | None = None
    metadata: MiniMaxProviderMetadata = field(default_factory=MiniMaxProviderMetadata)
    event_type: Literal["task_finished"] = field(default="task_finished", init=False)


@dataclass(frozen=True, slots=True)
class MiniMaxProviderErrorEvent:
    provider_event: str
    status: MiniMaxBaseResponse
    trace_id: str | None = None
    request_id: str | None = None
    event_type: Literal["provider_error"] = field(default="provider_error", init=False)


@dataclass(frozen=True, slots=True)
class MiniMaxSocketClosed:
    code: int | None
    reason_sha256: str | None = None
    reason_chars: int | None = None
    event_type: Literal["socket_closed"] = field(default="socket_closed", init=False)

    @classmethod
    def from_transport(cls, code: int | None, reason: str | None) -> MiniMaxSocketClosed:
        summary = _secret_summary(reason)
        return cls(code=code, reason_sha256=summary[0], reason_chars=summary[1])


@dataclass(frozen=True, slots=True)
class MiniMaxUnknownEvent:
    provider_event: str | None
    safe_fields: dict[str, object]
    status: MiniMaxBaseResponse | None = None
    trace_id: str | None = None
    request_id: str | None = None
    event_type: Literal["unknown"] = field(default="unknown", init=False)


type MiniMaxInboundEvent = (
    MiniMaxConnectedSuccess
    | MiniMaxTaskStarted
    | MiniMaxTaskContinued
    | MiniMaxAudioEvent
    | MiniMaxTaskFinished
    | MiniMaxProviderErrorEvent
    | MiniMaxSocketClosed
    | MiniMaxUnknownEvent
)


def decode_audio_payload(payload: object) -> bytes:
    """Decode the hex audio representation verified by the Task 002 provider evidence."""

    if not isinstance(payload, str) or not payload:
        raise MiniMaxAudioPayloadError("MiniMax audio payload must be a non-empty hex string")
    try:
        return bytes.fromhex(payload)
    except ValueError as exc:
        raise MiniMaxAudioPayloadError("MiniMax audio payload is not valid hex") from exc


def parse_minimax_event(raw: str | bytes) -> MiniMaxInboundEvent:
    """Parse one provider JSON message without retaining raw sensitive content."""

    text = _decode_raw_message(raw)
    try:
        decoded = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MiniMaxMalformedEventError("MiniMax event is malformed JSON") from exc
    if not isinstance(decoded, dict):
        raise MiniMaxMalformedEventError("MiniMax event must be a JSON object")
    payload = _string_key_mapping(decoded)
    provider_event = payload.get("event")
    event_name = provider_event if isinstance(provider_event, str) else None

    status_required = event_name in {
        "connected_success",
        "task_started",
        "task_continued",
        "task_finished",
        "task_failed",
    }
    status = _parse_base_response(payload.get("base_resp"), required=status_required)
    trace_id = _optional_string(payload.get("trace_id"))
    request_id = _optional_string(payload.get("request_id"))

    if event_name == "task_failed" or (status is not None and status.status_code != 0):
        if status is None:
            raise MiniMaxMalformedEventError("provider error is missing base_resp")
        failure = MiniMaxProviderErrorEvent(event_name or "unknown", status, trace_id, request_id)
        if status.status_code == 2206:
            raise MiniMaxUnsupportedReuseError(failure)
        raise MiniMaxProviderError(failure)

    if status is None and status_required:
        raise MiniMaxMalformedEventError(f"{event_name} is missing base_resp")
    if event_name == "connected_success":
        return MiniMaxConnectedSuccess(_required_status(status), trace_id, request_id)
    if event_name == "task_started":
        return MiniMaxTaskStarted(_required_status(status), trace_id, request_id)

    audio_payload = _extract_audio_payload(payload)
    if audio_payload is not None:
        return MiniMaxAudioEvent(
            provider_event=event_name or "unknown",
            audio=decode_audio_payload(audio_payload),
            status=status or MiniMaxBaseResponse(0),
            is_final=_optional_bool(payload.get("is_final")),
            trace_id=trace_id,
            request_id=request_id,
            metadata=_parse_metadata(payload.get("extra_info")),
        )
    if event_name == "task_continued":
        return MiniMaxTaskContinued(
            _required_status(status), _optional_bool(payload.get("is_final")), trace_id, request_id
        )
    if event_name == "task_finished":
        return MiniMaxTaskFinished(
            _required_status(status),
            trace_id,
            request_id,
            _parse_metadata(payload.get("extra_info")),
        )
    return MiniMaxUnknownEvent(
        provider_event=event_name,
        safe_fields=redact_mapping(payload),
        status=status,
        trace_id=trace_id,
        request_id=request_id,
    )


def redact_mapping(payload: dict[str, object]) -> dict[str, object]:
    """Return recursively sanitized fields suitable for logs and unknown-event fallback."""

    return {key: _redact_value(key, value) for key, value in payload.items()}


def _redact_value(key: str, value: object) -> object:
    normalized = key.lower()
    if normalized in {"api_key", "authorization", "token", "access_token"}:
        return "[REDACTED]"
    if normalized in {"voice_id", "audio", "text", "message", "status_msg"}:
        if isinstance(value, (str, bytes)):
            digest, size = _secret_summary(value)
            return {"sha256": digest, "chars_or_bytes": size}
        return "[REDACTED]"
    if isinstance(value, dict):
        return redact_mapping(_string_key_mapping(value))
    if isinstance(value, list):
        return [_redact_value(key, item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return f"<{type(value).__name__}>"


def _decode_raw_message(raw: str | bytes) -> str:
    if isinstance(raw, str):
        return raw
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MiniMaxMalformedEventError("MiniMax event bytes are not UTF-8 JSON") from exc


def _string_key_mapping(value: dict[object, object]) -> dict[str, object]:
    return {str(key): item for key, item in value.items()}


def _parse_base_response(value: object, *, required: bool) -> MiniMaxBaseResponse | None:
    if value is None and not required:
        return None
    if not isinstance(value, dict):
        raise MiniMaxMalformedEventError("base_resp must be an object")
    status_code = value.get("status_code")
    if not isinstance(status_code, int) or isinstance(status_code, bool):
        raise MiniMaxMalformedEventError("base_resp.status_code must be an integer")
    message = value.get("status_msg")
    if message is not None and not isinstance(message, str):
        raise MiniMaxMalformedEventError("base_resp.status_msg must be a string")
    digest, size = _secret_summary(message)
    return MiniMaxBaseResponse(status_code, digest, size)


def _parse_metadata(value: object) -> MiniMaxProviderMetadata:
    if value is None:
        return MiniMaxProviderMetadata()
    if not isinstance(value, dict):
        raise MiniMaxMalformedEventError("extra_info must be an object")
    return MiniMaxProviderMetadata(
        audio_format=_optional_string(value.get("audio_format")),
        sample_rate=_optional_integer(value.get("audio_sample_rate")),
        channel_count=_optional_integer(value.get("audio_channel")),
        audio_length_ms=_optional_integer(value.get("audio_length")),
    )


def _extract_audio_payload(payload: dict[str, object]) -> object | None:
    data = payload.get("data")
    if data is None:
        return None
    if not isinstance(data, dict):
        raise MiniMaxMalformedEventError("data must be an object")
    data_fields = _string_key_mapping(data)
    if "audio" not in data_fields:
        return None
    return data_fields["audio"]


def _required_status(status: MiniMaxBaseResponse | None) -> MiniMaxBaseResponse:
    if status is None:
        raise MiniMaxMalformedEventError("known event is missing base_resp")
    return status


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _optional_integer(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _optional_bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _secret_summary(value: str | bytes | None) -> tuple[str | None, int | None]:
    if value is None:
        return None, None
    encoded = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(encoded).hexdigest()[:12], len(value)


def _short_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:12]
