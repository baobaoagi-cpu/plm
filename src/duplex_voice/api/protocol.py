"""Strict, versioned, provider-free WebSocket protocol contracts."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    StringConstraints,
    TypeAdapter,
    ValidationError,
)

type SafeId = Annotated[
    str, StringConstraints(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
]
type SafeReason = Annotated[
    str, StringConstraints(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_.-]*$")
]


class ProtocolViolation(ValueError):
    """A safe public error that never echoes an invalid frame."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class _Frame(_StrictModel):
    protocol_version: Literal["1"]
    session_id: SafeId
    message_id: SafeId
    sequence: Annotated[int, Field(ge=1)]


class CallStartPayload(_StrictModel):
    call_grant: SecretStr
    client_capabilities: tuple[SafeId, ...] = ()


class CallStartFrame(_Frame):
    type: Literal["call.start"]
    generation_id: None = None
    payload: CallStartPayload


class AudioInputPayload(_StrictModel):
    timestamp_monotonic_ms: Annotated[int, Field(ge=0)]
    encoding: Literal["pcm_s16le"]
    sample_rate: Literal[16000]
    channels: Literal[1]
    frame_duration_ms: Literal[20]
    payload_length: Annotated[int, Field(gt=0, le=65_536)]


class AudioInputFrame(_Frame):
    type: Literal["audio.input"]
    generation_id: None = None
    payload: AudioInputPayload


class GenerationInterruptPayload(_StrictModel):
    reason: SafeReason


class GenerationInterruptFrame(_Frame):
    type: Literal["generation.interrupt"]
    generation_id: SafeId
    payload: GenerationInterruptPayload


class PlaybackDrainedPayload(_StrictModel):
    last_audio_sequence: Annotated[int, Field(ge=0)]


class PlaybackDrainedFrame(_Frame):
    type: Literal["playback.drained"]
    generation_id: SafeId
    payload: PlaybackDrainedPayload


class CallEndPayload(_StrictModel):
    reason: SafeReason


class CallEndFrame(_Frame):
    type: Literal["call.end"]
    generation_id: None = None
    payload: CallEndPayload


class HeartbeatPayload(_StrictModel):
    sent_at_monotonic_ms: Annotated[int, Field(ge=0)]


class HeartbeatFrame(_Frame):
    type: Literal["heartbeat"]
    generation_id: None = None
    payload: HeartbeatPayload


type ClientFrame = Annotated[
    CallStartFrame
    | AudioInputFrame
    | GenerationInterruptFrame
    | PlaybackDrainedFrame
    | CallEndFrame
    | HeartbeatFrame,
    Field(discriminator="type"),
]


class CallReadyPayload(_StrictModel):
    input_encoding: Literal["pcm_s16le"] = "pcm_s16le"
    input_sample_rate: Literal[16000] = 16000
    input_channels: Literal[1] = 1
    output_encoding: Literal["mp3"] = "mp3"
    output_sample_rate: Literal[24000] = 24000
    output_channels: Literal[1] = 1
    max_frame_bytes: Annotated[int, Field(ge=1_024)]


class CallReadyFrame(_Frame):
    type: Literal["call.ready"]
    generation_id: None = None
    payload: CallReadyPayload


class StateChangedPayload(_StrictModel):
    state: SafeId
    revision: Annotated[int, Field(ge=1)]


class StateChangedFrame(_Frame):
    type: Literal["state.changed"]
    generation_id: SafeId | None
    payload: StateChangedPayload


class TranscriptPayload(_StrictModel):
    text: SecretStr
    revision: Annotated[int, Field(ge=1)]


class TranscriptPartialFrame(_Frame):
    type: Literal["transcript.partial"]
    generation_id: None = None
    payload: TranscriptPayload


class TranscriptFinalFrame(_Frame):
    type: Literal["transcript.final"]
    generation_id: None = None
    payload: TranscriptPayload


class AudioOutputPayload(_StrictModel):
    audio_sequence: Annotated[int, Field(ge=1)]
    payload_length: Annotated[int, Field(gt=0, le=65_536)]
    encoding: Literal["mp3"] = "mp3"


class AudioOutputFrame(_Frame):
    type: Literal["audio.output"]
    generation_id: SafeId
    payload: AudioOutputPayload


class GenerationFinishedPayload(_StrictModel):
    audio_chunks: Annotated[int, Field(ge=0)]
    audio_bytes: Annotated[int, Field(ge=0)]


class GenerationFinishedFrame(_Frame):
    type: Literal["generation.finished"]
    generation_id: SafeId
    payload: GenerationFinishedPayload


class PlaybackClearPayload(_StrictModel):
    reason: SafeReason


class PlaybackClearFrame(_Frame):
    type: Literal["playback.clear"]
    generation_id: SafeId
    payload: PlaybackClearPayload


class CallEndedPayload(_StrictModel):
    reason: SafeReason


class CallEndedFrame(_Frame):
    type: Literal["call.ended"]
    generation_id: None = None
    payload: CallEndedPayload


class ErrorPayload(_StrictModel):
    code: SafeReason
    message: Annotated[str, StringConstraints(min_length=1, max_length=160)]
    retryable: bool
    trace_id: SafeId


class ErrorFrame(_Frame):
    type: Literal["error"]
    generation_id: SafeId | None
    payload: ErrorPayload


type ServerFrame = Annotated[
    CallReadyFrame
    | StateChangedFrame
    | TranscriptPartialFrame
    | TranscriptFinalFrame
    | AudioOutputFrame
    | GenerationFinishedFrame
    | PlaybackClearFrame
    | CallEndedFrame
    | ErrorFrame,
    Field(discriminator="type"),
]

_CLIENT_FRAME_ADAPTER: TypeAdapter[ClientFrame] = TypeAdapter(ClientFrame)
_SERVER_FRAME_ADAPTER: TypeAdapter[ServerFrame] = TypeAdapter(ServerFrame)


def parse_client_frame(raw: str | bytes, *, max_frame_bytes: int = 65_536) -> ClientFrame:
    """Parse one JSON control frame without echoing sensitive invalid input."""

    if max_frame_bytes < 1_024:
        raise ValueError("max_frame_bytes must be at least 1024")
    encoded = raw.encode("utf-8") if isinstance(raw, str) else raw
    if len(encoded) > max_frame_bytes:
        raise ProtocolViolation("frame exceeds the negotiated size limit")
    try:
        return _CLIENT_FRAME_ADAPTER.validate_json(encoded)
    except (ValidationError, UnicodeDecodeError, ValueError):
        raise ProtocolViolation("invalid protocol v1 client frame") from None


def validate_server_frame(frame: ServerFrame) -> ServerFrame:
    """Revalidate a server frame before it crosses the transport boundary."""

    try:
        return _SERVER_FRAME_ADAPTER.validate_python(frame)
    except ValidationError:
        raise ProtocolViolation("invalid protocol v1 server frame") from None


__all__ = [
    "AudioInputFrame",
    "AudioOutputFrame",
    "CallEndFrame",
    "CallEndedFrame",
    "CallReadyFrame",
    "CallStartFrame",
    "ClientFrame",
    "ErrorFrame",
    "GenerationFinishedFrame",
    "GenerationInterruptFrame",
    "HeartbeatFrame",
    "PlaybackClearFrame",
    "PlaybackDrainedFrame",
    "ProtocolViolation",
    "ServerFrame",
    "StateChangedFrame",
    "TranscriptFinalFrame",
    "TranscriptPartialFrame",
    "parse_client_frame",
    "validate_server_frame",
]
