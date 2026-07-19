"""Authenticated MiniMax T2A WebSocket spike.

This is deliberately independent from Pipecat and LiveKit. It records observed
provider behavior without defining the production protocol layer from Task 003.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import ssl
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Never

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed

DEFAULT_WS_URL = "wss://api.minimax.io/ws/v1/t2a_v2"
SUPPORTED_FORMATS = frozenset({"mp3", "pcm", "flac"})


class SpikeError(RuntimeError):
    """Expected configuration or provider failure with a safe message."""


@dataclass(frozen=True, slots=True)
class SpikeConfig:
    api_key: str = field(repr=False)
    model: str
    voice_id: str = field(repr=False)
    output_format: str
    sample_rate: int
    bitrate: int
    channel: int
    speed: float
    volume: float
    pitch: int
    language_boost: str | None
    ws_url: str
    connect_timeout_s: float
    receive_timeout_s: float

    @classmethod
    def from_environment(cls) -> SpikeConfig:
        """Load all provider settings from environment variables."""
        api_key = _required_env("MINIMAX_API_KEY")
        model = _required_env("MINIMAX_MODEL")
        voice_id = _required_env("MINIMAX_VOICE_ID")
        output_format = _required_env("MINIMAX_OUTPUT_FORMAT").lower()
        if output_format not in SUPPORTED_FORMATS:
            allowed = ", ".join(sorted(SUPPORTED_FORMATS))
            raise SpikeError(f"MINIMAX_OUTPUT_FORMAT must be one of: {allowed}")

        ws_url = os.getenv("MINIMAX_WS_URL", DEFAULT_WS_URL).strip()
        if not ws_url.startswith("wss://"):
            raise SpikeError("MINIMAX_WS_URL must use wss://")

        return cls(
            api_key=api_key,
            model=model,
            voice_id=voice_id,
            output_format=output_format,
            sample_rate=_int_env("MINIMAX_SAMPLE_RATE", 24_000, minimum=8_000),
            bitrate=_int_env("MINIMAX_BITRATE", 128_000, minimum=1),
            channel=_int_env("MINIMAX_CHANNELS", 1, minimum=1),
            speed=_float_env("MINIMAX_SPEED", 1.0),
            volume=_float_env("MINIMAX_VOLUME", 1.0),
            pitch=_int_env("MINIMAX_PITCH", 0),
            language_boost=_optional_env("MINIMAX_LANGUAGE_BOOST"),
            ws_url=ws_url,
            connect_timeout_s=_float_env("MINIMAX_CONNECT_TIMEOUT_S", 10.0, minimum=0.1),
            receive_timeout_s=_float_env("MINIMAX_RECEIVE_TIMEOUT_S", 30.0, minimum=0.1),
        )

    @property
    def voice_id_hash(self) -> str:
        return hashlib.sha256(self.voice_id.encode()).hexdigest()[:12]


@dataclass(slots=True)
class SpikeResult:
    probe_id: str
    generation_id: str
    reuse_generation_id: str | None
    mode: str
    model: str
    voice_id_hash: str
    requested_format: str
    requested_sample_rate: int
    connected_ms: float | None = None
    task_started_ms: float | None = None
    ttfa_ms: float | None = None
    completed_ms: float | None = None
    chunk_count: int = 0
    audio_bytes: int = 0
    chunk_sizes: list[int] = field(default_factory=list)
    observed_audio_format: str | None = None
    observed_sample_rate: int | None = None
    observed_channel: int | None = None
    observed_audio_length_ms: int | None = None
    detected_container: str = "unknown"
    first_chunk_independently_framed: bool | None = None
    task_continue_count: int = 0
    task_finished_received: bool = False
    provider_closed_after_finish: bool = False
    close_after_first_audio_completed: bool | None = None
    reuse_probe_event: str | None = None
    reuse_task_started: bool | None = None
    reuse_second_audio_received: bool | None = None
    reuse_ttfa_ms: float | None = None
    late_messages_after_close: int = 0
    late_audio_chunks_after_close: int = 0
    post_close_observation_ms: float | None = None
    client_connection_terminal_after_close: bool | None = None
    close_code: int | None = None
    first_chunk_path: str | None = None
    provider_status_codes: list[int] = field(default_factory=list)
    event_sequence: list[str] = field(default_factory=list)
    status: str = "started"
    error: str | None = None


class JsonEventLogger:
    """Emit a deliberately small, content-free structured event stream."""

    def __init__(self, *, voice_id_hash: str, probe_id: str, generation_id: str) -> None:
        self._voice_id_hash = voice_id_hash
        self._probe_id = probe_id
        self._generation_id = generation_id
        self._started = time.monotonic()

    def emit(self, event: str, **fields: object) -> None:
        record: dict[str, object] = {
            "event": event,
            "elapsed_ms": round((time.monotonic() - self._started) * 1000, 3),
            "voice_id_hash": self._voice_id_hash,
            "probe_id": self._probe_id,
            "generation_id": self._generation_id,
        }
        record.update(fields)
        print(json.dumps(record, ensure_ascii=False, separators=(",", ":")), flush=True)


class StreamPlayer:
    """Optional mpv stdin player; provider secrets never reach the child process."""

    def __init__(self, config: SpikeConfig, enabled: bool) -> None:
        self._config = config
        self._enabled = enabled
        self._process: subprocess.Popen[bytes] | None = None

    def start(self) -> None:
        if not self._enabled:
            return
        executable = shutil.which("mpv")
        if executable is None:
            raise SpikeError("--play requires mpv on PATH")
        command = [executable, "--no-cache", "--no-terminal", "--really-quiet"]
        if self._config.output_format == "pcm":
            command.extend(
                [
                    "--demuxer=rawaudio",
                    "--demuxer-rawaudio-format=s16le",
                    f"--demuxer-rawaudio-rate={self._config.sample_rate}",
                    f"--demuxer-rawaudio-channels={self._config.channel}",
                ]
            )
        command.append("-")
        self._process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def write(self, audio: bytes) -> None:
        if self._process is None or self._process.stdin is None:
            return
        self._process.stdin.write(audio)
        self._process.stdin.flush()

    def close(self) -> None:
        process = self._process
        if process is None:
            return
        if process.stdin is not None and not process.stdin.closed:
            process.stdin.close()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=5)
        finally:
            self._process = None


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SpikeError(f"required environment variable is missing: {name}")
    return value


def _optional_env(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def _int_env(name: str, default: int, *, minimum: int | None = None) -> int:
    raw = os.getenv(name)
    try:
        value = default if raw is None or not raw.strip() else int(raw)
    except ValueError as exc:
        raise SpikeError(f"{name} must be an integer") from exc
    if minimum is not None and value < minimum:
        raise SpikeError(f"{name} must be >= {minimum}")
    return value


def _float_env(name: str, default: float, *, minimum: float | None = None) -> float:
    raw = os.getenv(name)
    try:
        value = default if raw is None or not raw.strip() else float(raw)
    except ValueError as exc:
        raise SpikeError(f"{name} must be a number") from exc
    if minimum is not None and value < minimum:
        raise SpikeError(f"{name} must be >= {minimum}")
    return value


def build_task_start(config: SpikeConfig) -> dict[str, object]:
    message: dict[str, object] = {
        "event": "task_start",
        "model": config.model,
        "voice_setting": {
            "voice_id": config.voice_id,
            "speed": config.speed,
            "vol": config.volume,
            "pitch": config.pitch,
        },
        "audio_setting": {
            "sample_rate": config.sample_rate,
            "bitrate": config.bitrate,
            "format": config.output_format,
            "channel": config.channel,
        },
    }
    if config.language_boost is not None:
        message["language_boost"] = config.language_boost
    return message


def split_text(text: str, chunks: int) -> list[str]:
    """Split text into sequential, non-empty task_continue payloads."""
    normalized = text.strip()
    if not normalized:
        raise SpikeError("spike text must not be empty")
    if chunks < 1:
        raise SpikeError("--chunks must be >= 1")
    if chunks == 1 or len(normalized) == 1:
        return [normalized]
    width = max(1, (len(normalized) + chunks - 1) // chunks)
    return [normalized[index : index + width] for index in range(0, len(normalized), width)]


def decode_audio(response: dict[str, Any]) -> bytes:
    data = response.get("data")
    if not isinstance(data, dict):
        return b""
    audio = data.get("audio")
    if not isinstance(audio, str) or not audio:
        return b""
    try:
        return bytes.fromhex(audio)
    except ValueError as exc:
        raise SpikeError("provider returned non-hex audio data") from exc


def detect_container(audio: bytes) -> str:
    if audio.startswith(b"RIFF") and audio[8:12] == b"WAVE":
        return "wav"
    if audio.startswith(b"fLaC"):
        return "flac"
    if audio.startswith(b"ID3"):
        return "mp3-id3"
    if len(audio) >= 2 and audio[0] == 0xFF and audio[1] & 0xE0 == 0xE0:
        return "mp3-frame"
    return "raw-or-continuation"


def safe_provider_fields(response: dict[str, Any]) -> dict[str, object]:
    """Extract only non-content fields that are safe for logs and reports."""
    base_resp = response.get("base_resp")
    status_code: object = None
    status_msg: object = None
    if isinstance(base_resp, dict):
        status_code = base_resp.get("status_code")
        status_msg = base_resp.get("status_msg")
    fields: dict[str, object] = {
        "provider_event": response.get("event"),
        "trace_id": response.get("trace_id"),
        "status_code": status_code,
        "is_final": response.get("is_final"),
        "has_audio": bool(decode_audio(response)),
    }
    if isinstance(status_msg, str) and status_msg:
        fields["status_msg_sha256"] = hashlib.sha256(status_msg.encode()).hexdigest()[:12]
        fields["status_msg_chars"] = len(status_msg)
    return {key: value for key, value in fields.items() if value is not None}


async def receive_json(ws: ClientConnection, timeout_s: float) -> dict[str, Any]:
    try:
        async with asyncio.timeout(timeout_s):
            raw = await ws.recv()
    except TimeoutError as exc:
        raise SpikeError(f"provider receive timeout after {timeout_s:g}s") from exc
    if not isinstance(raw, str):
        raise SpikeError("provider returned a non-text WebSocket message")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SpikeError("provider returned malformed JSON") from exc
    if not isinstance(parsed, dict):
        raise SpikeError("provider returned a non-object JSON message")
    return parsed


def ensure_success(response: dict[str, Any], expected_event: str) -> None:
    event = response.get("event")
    base_resp = response.get("base_resp")
    status_code = base_resp.get("status_code") if isinstance(base_resp, dict) else None
    if event == "task_failed" or status_code not in (None, 0):
        raise SpikeError(f"provider failure: event={event!r}, code={status_code!r}")
    if event != expected_event:
        raise SpikeError(f"expected provider event {expected_event!r}, received {event!r}")


def _apply_extra_info(result: SpikeResult, response: dict[str, Any]) -> None:
    extra = response.get("extra_info")
    if not isinstance(extra, dict):
        return
    result.observed_audio_format = _optional_str(extra.get("audio_format"))
    result.observed_sample_rate = _optional_int(extra.get("audio_sample_rate"))
    result.observed_channel = _optional_int(extra.get("audio_channel"))
    result.observed_audio_length_ms = _optional_int(extra.get("audio_length"))


def _record_provider_status(result: SpikeResult, response: dict[str, Any]) -> None:
    base_resp = response.get("base_resp")
    if not isinstance(base_resp, dict):
        return
    status_code = _optional_int(base_resp.get("status_code"))
    if status_code is not None:
        result.provider_status_codes.append(status_code)


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def reuse_probe_ready(*, final_count: int, expected_count: int, already_sent: bool) -> bool:
    return not already_sent and final_count >= expected_count


async def run_spike(
    config: SpikeConfig,
    *,
    probe_id: str,
    generation_id: str,
    reuse_generation_id: str | None,
    text_chunks: list[str],
    output_path: Path,
    play: bool,
    close_after_first_audio: bool,
    probe_reuse: bool,
    overwrite: bool,
) -> SpikeResult:
    """Run one authenticated provider session and return redacted observations."""
    ensure_output_path_available(output_path, overwrite=overwrite)
    if close_after_first_audio:
        mode = "close_after_first_audio"
    elif probe_reuse:
        mode = "reuse_probe"
    else:
        mode = "standard"
    result = SpikeResult(
        probe_id=probe_id,
        generation_id=generation_id,
        reuse_generation_id=reuse_generation_id,
        mode=mode,
        model=config.model,
        voice_id_hash=config.voice_id_hash,
        requested_format=config.output_format,
        requested_sample_rate=config.sample_rate,
    )
    logger = JsonEventLogger(
        voice_id_hash=config.voice_id_hash,
        probe_id=probe_id,
        generation_id=generation_id,
    )
    player = StreamPlayer(config, play)
    audio = bytearray()
    started = time.monotonic()
    first_continue_sent: float | None = None
    first_chunk: bytes | None = None
    file_mode = "wb" if overwrite else "xb"

    result.event_sequence.append("spike_start")
    logger.emit("spike_start", mode=mode, model=config.model, output_format=config.output_format)
    player.start()
    try:
        ssl_context = ssl.create_default_context()
        async with connect(
            config.ws_url,
            additional_headers={"Authorization": f"Bearer {config.api_key}"},
            ssl=ssl_context,
            open_timeout=config.connect_timeout_s,
            close_timeout=5,
            max_size=16 * 1024 * 1024,
        ) as ws:
            connected = await receive_json(ws, config.receive_timeout_s)
            ensure_success(connected, "connected_success")
            _record_provider_status(result, connected)
            result.event_sequence.append("connected_success")
            result.connected_ms = (time.monotonic() - started) * 1000
            logger.emit("connected", **safe_provider_fields(connected))

            await ws.send(json.dumps(build_task_start(config), ensure_ascii=False))
            task_started = await receive_json(ws, config.receive_timeout_s)
            ensure_success(task_started, "task_started")
            _record_provider_status(result, task_started)
            result.event_sequence.append("task_started")
            result.task_started_ms = (time.monotonic() - started) * 1000
            logger.emit("task_started", **safe_provider_fields(task_started))

            for index, chunk in enumerate(text_chunks):
                if first_continue_sent is None:
                    first_continue_sent = time.monotonic()
                await ws.send(
                    json.dumps({"event": "task_continue", "text": chunk}, ensure_ascii=False)
                )
                result.task_continue_count += 1
                result.event_sequence.append(f"task_continue_sent:{index + 1}")
                logger.emit(
                    "task_continue_sent",
                    chunk_index=index,
                    text_chars=len(chunk),
                    text_sha256=hashlib.sha256(chunk.encode()).hexdigest()[:12],
                )

            if not close_after_first_audio and not probe_reuse:
                await ws.send(json.dumps({"event": "task_finish"}))
                result.event_sequence.append("task_finish_sent")
                logger.emit("task_finish_sent")

            reuse_sent = False
            reuse_phase = False
            reuse_continue_sent: float | None = None
            initial_final_count = 0
            while True:
                try:
                    response = await receive_json(ws, config.receive_timeout_s)
                except ConnectionClosed:
                    result.provider_closed_after_finish = not close_after_first_audio
                    logger.emit("provider_connection_closed")
                    break
                logger.emit("provider_message", **safe_provider_fields(response))
                _record_provider_status(result, response)
                provider_event = _optional_str(response.get("event"))
                if provider_event is not None:
                    result.event_sequence.append(provider_event)

                if response.get("event") == "task_failed":
                    ensure_success(response, "task_finished")

                chunk_bytes = decode_audio(response)
                if chunk_bytes:
                    if result.chunk_count == 0:
                        first_chunk = chunk_bytes
                        if first_continue_sent is None:
                            raise SpikeError("received audio before task_continue")
                        result.ttfa_ms = (time.monotonic() - first_continue_sent) * 1000
                        result.detected_container = detect_container(chunk_bytes)
                        result.first_chunk_independently_framed = (
                            result.detected_container != "raw-or-continuation"
                        )
                        logger.emit(
                            "first_audio",
                            ttfa_ms=round(result.ttfa_ms, 3),
                            detected_container=result.detected_container,
                            chunk_bytes=len(chunk_bytes),
                        )
                        result.event_sequence.append("first_audio")
                    result.event_sequence.append("audio_chunk")
                    result.chunk_count += 1
                    result.chunk_sizes.append(len(chunk_bytes))
                    result.audio_bytes += len(chunk_bytes)
                    audio.extend(chunk_bytes)
                    player.write(chunk_bytes)
                    if reuse_phase:
                        if (
                            result.reuse_second_audio_received is False
                            and reuse_continue_sent is not None
                        ):
                            result.reuse_ttfa_ms = (time.monotonic() - reuse_continue_sent) * 1000
                        result.reuse_second_audio_received = True

                    if close_after_first_audio:
                        result.event_sequence.append("socket_close_sent")
                        await ws.close(code=1000, reason="spike cancellation probe")
                        result.close_after_first_audio_completed = True
                        logger.emit("socket_closed_after_first_audio")
                        result.event_sequence.append("socket_closed_after_first_audio")
                        observation_started = time.monotonic()
                        try:
                            async with asyncio.timeout(0.5):
                                while True:
                                    late_raw = await ws.recv()
                                    result.late_messages_after_close += 1
                                    if isinstance(late_raw, str):
                                        try:
                                            late_response = json.loads(late_raw)
                                        except json.JSONDecodeError:
                                            continue
                                        if isinstance(late_response, dict) and decode_audio(
                                            late_response
                                        ):
                                            result.late_audio_chunks_after_close += 1
                        except ConnectionClosed as exc:
                            result.client_connection_terminal_after_close = True
                            if exc.rcvd is not None:
                                result.close_code = exc.rcvd.code
                            result.event_sequence.append("post_close_connection_terminal")
                            logger.emit(
                                "post_close_connection_terminal",
                                late_messages=result.late_messages_after_close,
                                late_audio_chunks=result.late_audio_chunks_after_close,
                                close_code=result.close_code,
                            )
                        except TimeoutError:
                            result.client_connection_terminal_after_close = False
                            result.event_sequence.append("post_close_observation_timeout")
                            logger.emit(
                                "post_close_observation_timeout",
                                late_messages=result.late_messages_after_close,
                                late_audio_chunks=result.late_audio_chunks_after_close,
                            )
                        result.post_close_observation_ms = (
                            time.monotonic() - observation_started
                        ) * 1000
                        break

                _apply_extra_info(result, response)

                if probe_reuse and not reuse_phase and response.get("is_final") is True:
                    initial_final_count += 1
                    result.event_sequence.append(
                        f"initial_task_continue_final:{initial_final_count}"
                    )

                if probe_reuse and reuse_probe_ready(
                    final_count=initial_final_count,
                    expected_count=len(text_chunks),
                    already_sent=reuse_sent,
                ):
                    await ws.send(json.dumps(build_task_start(config), ensure_ascii=False))
                    reuse_sent = True
                    logger.emit("reuse_probe_task_start_sent")
                    reuse_response = await receive_json(ws, config.receive_timeout_s)
                    _record_provider_status(result, reuse_response)
                    result.reuse_probe_event = _optional_str(reuse_response.get("event"))
                    result.event_sequence.append(
                        f"reuse_probe_response:{result.reuse_probe_event or 'no_event'}"
                    )
                    logger.emit(
                        "reuse_probe_response",
                        reuse_generation_id=reuse_generation_id,
                        **safe_provider_fields(reuse_response),
                    )
                    result.reuse_task_started = reuse_response.get("event") == "task_started"
                    if not result.reuse_task_started:
                        await ws.close(code=1000, reason="reuse probe rejected")
                        break
                    reuse_phase = True
                    result.reuse_second_audio_received = False
                    second_text = text_chunks[0]
                    await ws.send(
                        json.dumps(
                            {"event": "task_continue", "text": second_text},
                            ensure_ascii=False,
                        )
                    )
                    reuse_continue_sent = time.monotonic()
                    result.task_continue_count += 1
                    result.event_sequence.append("reuse_task_continue_sent")
                    logger.emit(
                        "reuse_probe_task_continue_sent",
                        reuse_generation_id=reuse_generation_id,
                        text_chars=len(second_text),
                        text_sha256=hashlib.sha256(second_text.encode()).hexdigest()[:12],
                    )
                    await ws.send(json.dumps({"event": "task_finish"}))
                    result.event_sequence.append("reuse_task_finish_sent")
                    logger.emit("reuse_probe_task_finish_sent")
                    continue

                if response.get("event") == "task_finished":
                    result.task_finished_received = True
                    result.event_sequence.append("task_finished_received")
                    try:
                        async with asyncio.timeout(5):
                            await ws.wait_closed()
                        result.provider_closed_after_finish = True
                    except TimeoutError:
                        logger.emit("provider_close_timeout_after_task_finished")
                    break

            result.completed_ms = (time.monotonic() - started) * 1000
            result.status = "complete"
    except Exception as exc:
        result.status = "failed"
        result.error = _safe_exception(exc)
        logger.emit("spike_failed", error=result.error, error_type=type(exc).__name__)
        raise
    finally:
        player.close()
        if audio:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open(file_mode) as output:
                output.write(audio)
            logger.emit("audio_saved", path=str(output_path), audio_bytes=len(audio))
        if first_chunk is not None:
            first_chunk_path = output_path.with_name(
                f"{output_path.stem}.first-chunk{output_path.suffix}"
            )
            with first_chunk_path.open(file_mode) as output:
                output.write(first_chunk)
            result.first_chunk_path = str(first_chunk_path)
            logger.emit(
                "first_chunk_saved",
                path=str(first_chunk_path),
                audio_bytes=len(first_chunk),
            )
        logger.emit("spike_cleanup_complete")
    return result


def _safe_exception(exc: BaseException) -> str:
    message = str(exc)
    return message[:300] if message else type(exc).__name__


def ensure_output_path_available(path: Path, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise SpikeError(f"output file exists; pass --overwrite to replace it: {path}")


def write_json_result(path: Path, result: SpikeResult, *, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if overwrite else "x"
    with path.open(mode, encoding="utf-8") as output:
        json.dump(asdict(result), output, ensure_ascii=False, indent=2)
        output.write("\n")


def write_markdown_report(path: Path, result: SpikeResult, *, overwrite: bool) -> None:
    """Write only observed, redacted facts from a successful authenticated run."""
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if overwrite else "x"
    lines = [
        "# MiniMax WebSocket Spike Results",
        "",
        "> Generated from an authenticated run. No API key, full Voice ID, or input text "
        "is stored.",
        "",
        "## Run",
        "",
        f"- Status: `{result.status}`",
        f"- Probe ID: `{result.probe_id}`",
        f"- Generation ID: `{result.generation_id}`",
        f"- Reuse generation ID: `{result.reuse_generation_id}`",
        f"- Mode: `{result.mode}`",
        f"- Model: `{result.model}`",
        f"- Voice ID hash: `{result.voice_id_hash}`",
        f"- Requested audio: `{result.requested_format}`, {result.requested_sample_rate} Hz",
        f"- Observed audio: `{result.observed_audio_format}`, "
        f"{result.observed_sample_rate} Hz, channel {result.observed_channel}",
        f"- Detected first-chunk container: `{result.detected_container}`",
        f"- First chunk independently framed: `{result.first_chunk_independently_framed}`",
        "",
        "## Timing",
        "",
        f"- Connected: `{_format_ms(result.connected_ms)}`",
        f"- Task started: `{_format_ms(result.task_started_ms)}`",
        f"- TTFA: `{_format_ms(result.ttfa_ms)}`",
        f"- Completed: `{_format_ms(result.completed_ms)}`",
        "",
        "## Stream observations",
        "",
        f"- task_continue count: `{result.task_continue_count}`",
        f"- Audio chunks: `{result.chunk_count}`",
        f"- Audio bytes: `{result.audio_bytes}`",
        f"- Reported audio length: `{result.observed_audio_length_ms} ms`",
        f"- task_finished received: `{result.task_finished_received}`",
        f"- Provider closed after task_finish: `{result.provider_closed_after_finish}`",
        f"- Close-after-first-audio completed: `{result.close_after_first_audio_completed}`",
        f"- Late messages after close: `{result.late_messages_after_close}`",
        f"- Late audio chunks after close: `{result.late_audio_chunks_after_close}`",
        f"- Post-close observation: `{_format_ms(result.post_close_observation_ms)}`",
        "- Client connection terminal after close: "
        f"`{result.client_connection_terminal_after_close}`",
        f"- Close code: `{result.close_code}`",
        f"- Reuse probe response event: `{result.reuse_probe_event}`",
        f"- Reuse task started: `{result.reuse_task_started}`",
        f"- Reuse second audio received: `{result.reuse_second_audio_received}`",
        f"- Reuse TTFA: `{_format_ms(result.reuse_ttfa_ms)}`",
        f"- Provider status codes: `{result.provider_status_codes}`",
        f"- Event sequence: `{result.event_sequence}`",
        "",
        "## Required conclusion",
        "",
        "Run the standard, close-after-first-audio, and reuse-probe modes before accepting "
        "Task 002.",
        "Do not infer PCM byte order, independent chunk playability, cancellation semantics, "
        "or connection reuse from documentation alone.",
        "",
    ]
    with path.open(mode, encoding="utf-8") as output:
        output.write("\n".join(lines))


def _format_ms(value: float | None) -> str:
    return "not observed" if value is None else f"{value:.3f} ms"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    text_source = parser.add_mutually_exclusive_group()
    text_source.add_argument("--text", help="Text to synthesize; not written to logs or reports")
    text_source.add_argument("--text-file", type=Path, help="UTF-8 text file to synthesize")
    parser.add_argument("--chunks", type=int, default=2, help="Sequential task_continue count")
    parser.add_argument("--probe-id", required=True, help="Non-secret local probe identifier")
    parser.add_argument("--generation-id", required=True, help="Non-secret local generation ID")
    parser.add_argument(
        "--reuse-generation-id",
        help="Required non-secret second generation ID for --probe-reuse",
    )
    parser.add_argument("--output", type=Path, default=None, help="Audio output path")
    parser.add_argument(
        "--result-json",
        type=Path,
        default=Path("artifacts/minimax-spike-result.json"),
    )
    parser.add_argument("--report", type=Path, default=Path("docs/minimax-spike-results.md"))
    parser.add_argument("--play", action="store_true", help="Stream audio to mpv while saving")
    parser.add_argument(
        "--close-after-first-audio",
        action="store_true",
        help="Probe socket-close cancellation behavior",
    )
    parser.add_argument(
        "--probe-reuse",
        action="store_true",
        help="Probe a second task_start before task_finish",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing output and report files",
    )
    args = parser.parse_args(argv)
    if args.close_after_first_audio and args.probe_reuse:
        parser.error("--close-after-first-audio and --probe-reuse are mutually exclusive")
    if args.probe_reuse and not args.reuse_generation_id:
        parser.error("--probe-reuse requires --reuse-generation-id")
    return args


def load_text(args: argparse.Namespace) -> str:
    text = args.text
    if isinstance(text, str):
        return text
    text_file = args.text_file
    if isinstance(text_file, Path):
        return text_file.read_text(encoding="utf-8")
    return os.getenv("MINIMAX_SPIKE_TEXT", "請用自然的繁體中文說: 這是一段即時語音串流測試。")


async def async_main(args: argparse.Namespace) -> int:
    config = SpikeConfig.from_environment()
    text_chunks = split_text(load_text(args), args.chunks)
    output_path = args.output or Path(f"artifacts/minimax-spike.{config.output_format}")
    result = await run_spike(
        config,
        probe_id=str(args.probe_id),
        generation_id=str(args.generation_id),
        reuse_generation_id=(
            str(args.reuse_generation_id) if args.reuse_generation_id is not None else None
        ),
        text_chunks=text_chunks,
        output_path=output_path,
        play=bool(args.play),
        close_after_first_audio=bool(args.close_after_first_audio),
        probe_reuse=bool(args.probe_reuse),
        overwrite=bool(args.overwrite),
    )
    write_json_result(args.result_json, result, overwrite=bool(args.overwrite))
    write_markdown_report(args.report, result, overwrite=bool(args.overwrite))
    return 0


def _exit_with_error(message: str) -> Never:
    print(
        json.dumps({"event": "spike_configuration_error", "error": message}, ensure_ascii=False),
        file=sys.stderr,
    )
    raise SystemExit(2)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    try:
        raise SystemExit(asyncio.run(async_main(args)))
    except KeyboardInterrupt:
        print(json.dumps({"event": "spike_interrupted", "cleanup": "requested"}), file=sys.stderr)
        raise SystemExit(130) from None
    except SpikeError as exc:
        _exit_with_error(str(exc))


if __name__ == "__main__":
    main()
