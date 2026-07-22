"""Fail-closed configuration for the offline duplex hardening milestone."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from os import environ


class ConfigurationError(ValueError):
    """Raised when runtime configuration would weaken an approved boundary."""


class RuntimeMode(StrEnum):
    OFFLINE_HARDENING = "offline_hardening"
    STAGING_INTEGRATION = "staging_integration"


class ValueClass(StrEnum):
    SECRET = "secret"
    SENSITIVE_CONFIG = "sensitive_config"
    SERVER_CONFIG = "server_config"
    PUBLIC_CONFIG = "public_config"


@dataclass(frozen=True, slots=True)
class EnvironmentVariableContract:
    name: str
    value_class: ValueClass
    consumer: str
    required_when: str


_INTEGRATION_CONTRACT = (
    EnvironmentVariableContract(
        "XIEWENXIAN_CALIBRATION_LINE_CHANNEL_ID",
        ValueClass.PUBLIC_CONFIG,
        "identity_gateway",
        "liff_identity_enabled",
    ),
    EnvironmentVariableContract(
        "XIEWENXIAN_CALIBRATION_LINE_CHANNEL_SECRET",
        ValueClass.SECRET,
        "identity_gateway",
        "line_integration_enabled",
    ),
    EnvironmentVariableContract(
        "XIEWENXIAN_CALIBRATION_LINE_CHANNEL_ACCESS_TOKEN",
        ValueClass.SECRET,
        "line_adapter",
        "line_integration_enabled",
    ),
    EnvironmentVariableContract(
        "XIEWENXIAN_CALIBRATION_LIFF_ID",
        ValueClass.PUBLIC_CONFIG,
        "identity_gateway",
        "liff_identity_enabled",
    ),
    EnvironmentVariableContract(
        "XIEWENXIAN_CALIBRATION_LINE_ISSUER",
        ValueClass.PUBLIC_CONFIG,
        "identity_gateway",
        "liff_identity_enabled",
    ),
    EnvironmentVariableContract(
        "XIEWENXIAN_CALIBRATION_LINE_ALLOWLIST_JSON",
        ValueClass.SENSITIVE_CONFIG,
        "identity_gateway",
        "line_integration_enabled",
    ),
    EnvironmentVariableContract(
        "MINIMAX_API_KEY", ValueClass.SECRET, "voice_runtime", "providers_enabled"
    ),
    EnvironmentVariableContract(
        "MINIMAX_VOICE_ID", ValueClass.SECRET, "spike_only", "task_002_manual_probe"
    ),
    EnvironmentVariableContract(
        "MINIMAX_MODEL", ValueClass.SERVER_CONFIG, "voice_runtime", "providers_enabled"
    ),
    EnvironmentVariableContract(
        "XIEWENXIAN_CALIBRATION_MINIMAX_VOICE_ID",
        ValueClass.SECRET,
        "voice_runtime",
        "providers_enabled",
    ),
    EnvironmentVariableContract(
        "XIEWENXIAN_STT_API_KEY", ValueClass.SECRET, "voice_runtime", "providers_enabled"
    ),
    EnvironmentVariableContract(
        "XIEWENXIAN_LLM_API_KEY", ValueClass.SECRET, "voice_runtime", "providers_enabled"
    ),
    EnvironmentVariableContract(
        "XIEWENXIAN_STAGING_DATABASE_URL",
        ValueClass.SECRET,
        "voice_runtime",
        "database_enabled",
    ),
    EnvironmentVariableContract(
        "XIEWENXIAN_STAGING_ADMIN_READONLY_DATABASE_URL",
        ValueClass.SECRET,
        "admin_backend",
        "admin_database_enabled",
    ),
    EnvironmentVariableContract(
        "XIEWENXIAN_CALL_GRANT_SIGNING_KEY",
        ValueClass.SECRET,
        "identity_gateway",
        "line_integration_enabled",
    ),
    EnvironmentVariableContract(
        "XIEWENXIAN_ADMIN_SESSION_SECRET",
        ValueClass.SECRET,
        "admin_backend",
        "admin_http_enabled",
    ),
    EnvironmentVariableContract(
        "XIEWENXIAN_CALIBRATION_LIVEKIT_URL",
        ValueClass.SERVER_CONFIG,
        "transport",
        "livekit_enabled",
    ),
    EnvironmentVariableContract(
        "XIEWENXIAN_CALIBRATION_LIVEKIT_API_KEY",
        ValueClass.SECRET,
        "transport",
        "livekit_enabled",
    ),
    EnvironmentVariableContract(
        "XIEWENXIAN_CALIBRATION_LIVEKIT_API_SECRET",
        ValueClass.SECRET,
        "transport",
        "livekit_enabled",
    ),
    EnvironmentVariableContract(
        "VITE_LIFF_ID", ValueClass.PUBLIC_CONFIG, "browser", "line_integration_enabled"
    ),
    EnvironmentVariableContract(
        "VITE_WS_URL", ValueClass.PUBLIC_CONFIG, "browser", "line_integration_enabled"
    ),
)

_SERVER_SETTING_NAMES = (
    "APP_ENV",
    "LOG_LEVEL",
    "EXTERNAL_PROVIDERS_ENABLED",
    "LINE_INTEGRATION_ENABLED",
    "DATABASE_ENABLED",
    "ADMIN_DATABASE_ENABLED",
    "ADMIN_HTTP_ENABLED",
    "LIVEKIT_ENABLED",
    "LIFF_IDENTITY_ENABLED",
    "XIEWENXIAN_CALIBRATION_ENABLED",
    "XIEWENXIAN_CALIBRATION_KILL_SWITCH",
    "XIEWENXIAN_CALIBRATION_SANDBOX_MODE",
    "MINIMAX_OUTPUT_FORMAT",
    "MINIMAX_SAMPLE_RATE",
    "MINIMAX_CHANNELS",
    "XIEWENXIAN_STT_PROVIDER",
    "XIEWENXIAN_STT_MODEL",
    "XIEWENXIAN_STT_LANGUAGE",
    "XIEWENXIAN_LLM_PROVIDER",
    "XIEWENXIAN_LLM_MODEL",
    "XIEWENXIAN_STAGING_DB_SCHEMA",
    "VOICE_INPUT_SAMPLE_RATE",
    "VOICE_INPUT_CHANNELS",
    "VOICE_INPUT_SAMPLE_WIDTH_BYTES",
    "VOICE_INPUT_ENCODING",
    "VOICE_INPUT_FRAME_MS",
    "TTS_SESSION_STRATEGY",
    "GENERATION_GUARD_ENABLED",
    "STALE_GENERATION_POLICY",
    "ENABLE_INTERRUPTION",
    "MIN_OVERLAP_MS",
    "INTERRUPTION_CONFIRMATION_MS",
    "TTS_MAX_PENDING_AUDIO_MS",
    "CALL_INPUT_QUEUE_MAX_MS",
    "CALL_WS_MAX_FRAME_BYTES",
    "TEXT_CHUNK_MIN_CHARS",
    "TEXT_CHUNK_PREFERRED_CHARS",
    "TEXT_CHUNK_MAX_CHARS",
    "TEXT_CHUNK_MAX_WAIT_MS",
    "ENABLE_DEBUG_EVENTS",
    "ENABLE_AUDIO_DUMP",
)

ENVIRONMENT_CONTRACT = (
    *_INTEGRATION_CONTRACT,
    *(
        EnvironmentVariableContract(
            name, ValueClass.SERVER_CONFIG, "server", "runtime"
        )
        for name in _SERVER_SETTING_NAMES
    ),
)

SECRET_ENV_NAMES = frozenset(
    item.name
    for item in ENVIRONMENT_CONTRACT
    if item.value_class in {ValueClass.SECRET, ValueClass.SENSITIVE_CONFIG}
)
PUBLIC_BROWSER_ENV_NAMES = frozenset(
    item.name
    for item in ENVIRONMENT_CONTRACT
    if item.consumer == "browser" and item.value_class is ValueClass.PUBLIC_CONFIG
)


@dataclass(frozen=True, slots=True)
class RuntimeDefaults:
    """Non-secret defaults explicitly specified by the development specification."""

    voice_input_sample_rate: int = 16_000
    voice_input_channels: int = 1
    voice_input_sample_width_bytes: int = 2
    voice_input_encoding: str = "pcm_s16le"
    voice_input_frame_ms: int = 20
    minimax_sample_rate: int = 24_000
    minimax_channels: int = 1
    minimax_output_format: str = "mp3"
    tts_session_strategy: str = "one_session_per_generation"
    generation_guard_enabled: bool = True
    stale_generation_policy: str = "discard"
    enable_interruption: bool = True
    min_overlap_ms: int = 180
    interruption_confirmation_ms: int = 300
    tts_max_pending_audio_ms: int = 2_000
    input_queue_max_ms: int = 1_000
    websocket_max_frame_bytes: int = 65_536
    text_chunk_min_chars: int = 6
    text_chunk_preferred_chars: int = 16
    text_chunk_max_chars: int = 32
    text_chunk_max_wait_ms: int = 250
    enable_debug_events: bool = True
    enable_audio_dump: bool = False


@dataclass(frozen=True, slots=True)
class RuntimeConfiguration:
    """Validated settings with no secret values exposed through diagnostics."""

    mode: RuntimeMode
    app_env: str
    log_level: str
    providers_enabled: bool
    line_integration_enabled: bool
    database_enabled: bool
    admin_database_enabled: bool
    admin_http_enabled: bool
    livekit_enabled: bool
    sandbox_mode: bool
    kill_switch: bool
    defaults: RuntimeDefaults

    def redacted_snapshot(self) -> dict[str, object]:
        return {
            "mode": self.mode.value,
            "app_env": self.app_env,
            "log_level": self.log_level,
            "providers_enabled": self.providers_enabled,
            "line_integration_enabled": self.line_integration_enabled,
            "database_enabled": self.database_enabled,
            "admin_database_enabled": self.admin_database_enabled,
            "admin_http_enabled": self.admin_http_enabled,
            "livekit_enabled": self.livekit_enabled,
            "sandbox_mode": self.sandbox_mode,
            "kill_switch": self.kill_switch,
            "secret_slots_configured": 0,
            "voice_input_format": {
                "encoding": self.defaults.voice_input_encoding,
                "sample_rate": self.defaults.voice_input_sample_rate,
                "channels": self.defaults.voice_input_channels,
                "frame_ms": self.defaults.voice_input_frame_ms,
            },
            "voice_output_format": {
                "encoding": self.defaults.minimax_output_format,
                "sample_rate": self.defaults.minimax_sample_rate,
                "channels": self.defaults.minimax_channels,
            },
            "tts_session_strategy": self.defaults.tts_session_strategy,
            "generation_guard_enabled": self.defaults.generation_guard_enabled,
            "stale_generation_policy": self.defaults.stale_generation_policy,
        }


def _read_bool(
    environment: Mapping[str, str], name: str, *, default: bool
) -> bool:
    raw = environment.get(name)
    if raw is None:
        return default
    normalized = raw.strip().casefold()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(f"{name} must be a boolean")


def _read_int(
    environment: Mapping[str, str], name: str, *, default: int, minimum: int
) -> int:
    raw = environment.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer") from exc
    if value < minimum:
        raise ConfigurationError(f"{name} must be at least {minimum}")
    return value


def _require_nonempty(environment: Mapping[str, str], names: tuple[str, ...]) -> None:
    missing = sorted(name for name in names if not environment.get(name, "").strip())
    if missing:
        raise ConfigurationError("required configuration slots are missing: " + ", ".join(missing))


def load_runtime_configuration(
    environment: Mapping[str, str] = environ,
    *,
    mode: RuntimeMode = RuntimeMode.OFFLINE_HARDENING,
) -> RuntimeConfiguration:
    """Validate a configuration without contacting a provider or revealing a secret."""

    app_env = environment.get("APP_ENV", "development").strip().casefold()
    if app_env not in {"development", "test", "staging"}:
        raise ConfigurationError("Phase 3C permits development, test, or staging only")

    log_level = environment.get("LOG_LEVEL", "INFO").strip().upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ConfigurationError("LOG_LEVEL is invalid")

    providers_enabled = _read_bool(
        environment, "EXTERNAL_PROVIDERS_ENABLED", default=False
    )
    line_enabled = _read_bool(environment, "LINE_INTEGRATION_ENABLED", default=False)
    database_enabled = _read_bool(environment, "DATABASE_ENABLED", default=False)
    admin_database_enabled = _read_bool(
        environment, "ADMIN_DATABASE_ENABLED", default=False
    )
    admin_http_enabled = _read_bool(environment, "ADMIN_HTTP_ENABLED", default=False)
    livekit_enabled = _read_bool(environment, "LIVEKIT_ENABLED", default=False)
    sandbox_mode = _read_bool(
        environment, "XIEWENXIAN_CALIBRATION_SANDBOX_MODE", default=True
    )
    kill_switch = _read_bool(
        environment, "XIEWENXIAN_CALIBRATION_KILL_SWITCH", default=True
    )

    integration_flags = {
        "EXTERNAL_PROVIDERS_ENABLED": providers_enabled,
        "LINE_INTEGRATION_ENABLED": line_enabled,
        "DATABASE_ENABLED": database_enabled,
        "ADMIN_DATABASE_ENABLED": admin_database_enabled,
        "ADMIN_HTTP_ENABLED": admin_http_enabled,
        "LIVEKIT_ENABLED": livekit_enabled,
    }
    if mode is RuntimeMode.OFFLINE_HARDENING:
        enabled = sorted(name for name, value in integration_flags.items() if value)
        if enabled:
            raise ConfigurationError(
                "offline hardening forbids external integration flags: " + ", ".join(enabled)
            )
    if not sandbox_mode:
        raise ConfigurationError("owner calibration must remain in sandbox mode")
    if not kill_switch and mode is RuntimeMode.OFFLINE_HARDENING:
        raise ConfigurationError("offline hardening requires the kill switch")

    defaults = RuntimeDefaults(
        voice_input_sample_rate=_read_int(
            environment, "VOICE_INPUT_SAMPLE_RATE", default=16_000, minimum=8_000
        ),
        voice_input_channels=_read_int(
            environment, "VOICE_INPUT_CHANNELS", default=1, minimum=1
        ),
        voice_input_sample_width_bytes=_read_int(
            environment, "VOICE_INPUT_SAMPLE_WIDTH_BYTES", default=2, minimum=1
        ),
        voice_input_encoding=environment.get(
            "VOICE_INPUT_ENCODING", "pcm_s16le"
        ).strip(),
        voice_input_frame_ms=_read_int(
            environment, "VOICE_INPUT_FRAME_MS", default=20, minimum=1
        ),
        minimax_sample_rate=_read_int(
            environment, "MINIMAX_SAMPLE_RATE", default=24_000, minimum=8_000
        ),
        minimax_channels=_read_int(environment, "MINIMAX_CHANNELS", default=1, minimum=1),
        minimax_output_format=environment.get("MINIMAX_OUTPUT_FORMAT", "mp3")
        .strip()
        .casefold(),
        tts_session_strategy=environment.get(
            "TTS_SESSION_STRATEGY", "one_session_per_generation"
        )
        .strip()
        .casefold(),
        generation_guard_enabled=_read_bool(
            environment, "GENERATION_GUARD_ENABLED", default=True
        ),
        stale_generation_policy=environment.get(
            "STALE_GENERATION_POLICY", "discard"
        )
        .strip()
        .casefold(),
        enable_interruption=_read_bool(environment, "ENABLE_INTERRUPTION", default=True),
        min_overlap_ms=_read_int(
            environment, "MIN_OVERLAP_MS", default=180, minimum=1
        ),
        interruption_confirmation_ms=_read_int(
            environment, "INTERRUPTION_CONFIRMATION_MS", default=300, minimum=1
        ),
        tts_max_pending_audio_ms=_read_int(
            environment, "TTS_MAX_PENDING_AUDIO_MS", default=2_000, minimum=1
        ),
        input_queue_max_ms=_read_int(
            environment, "CALL_INPUT_QUEUE_MAX_MS", default=1_000, minimum=1
        ),
        websocket_max_frame_bytes=_read_int(
            environment, "CALL_WS_MAX_FRAME_BYTES", default=65_536, minimum=1_024
        ),
        text_chunk_min_chars=_read_int(
            environment, "TEXT_CHUNK_MIN_CHARS", default=6, minimum=1
        ),
        text_chunk_preferred_chars=_read_int(
            environment, "TEXT_CHUNK_PREFERRED_CHARS", default=16, minimum=1
        ),
        text_chunk_max_chars=_read_int(
            environment, "TEXT_CHUNK_MAX_CHARS", default=32, minimum=1
        ),
        text_chunk_max_wait_ms=_read_int(
            environment, "TEXT_CHUNK_MAX_WAIT_MS", default=250, minimum=1
        ),
        enable_debug_events=_read_bool(environment, "ENABLE_DEBUG_EVENTS", default=True),
        enable_audio_dump=_read_bool(environment, "ENABLE_AUDIO_DUMP", default=False),
    )
    _validate_duplex_invariants(defaults)

    if providers_enabled:
        _require_nonempty(
            environment,
            (
                "MINIMAX_API_KEY",
                "MINIMAX_MODEL",
                "XIEWENXIAN_CALIBRATION_MINIMAX_VOICE_ID",
                "XIEWENXIAN_STT_API_KEY",
                "XIEWENXIAN_STT_MODEL",
                "XIEWENXIAN_LLM_API_KEY",
                "XIEWENXIAN_LLM_MODEL",
            ),
        )
    if line_enabled:
        _require_nonempty(
            environment,
            (
                "XIEWENXIAN_CALIBRATION_LINE_CHANNEL_ID",
                "XIEWENXIAN_CALIBRATION_LINE_CHANNEL_SECRET",
                "XIEWENXIAN_CALIBRATION_LINE_CHANNEL_ACCESS_TOKEN",
                "XIEWENXIAN_CALIBRATION_LIFF_ID",
                "XIEWENXIAN_CALL_GRANT_SIGNING_KEY",
            ),
        )
    if database_enabled:
        _require_nonempty(environment, ("XIEWENXIAN_STAGING_DATABASE_URL",))
    if admin_database_enabled:
        _require_nonempty(
            environment, ("XIEWENXIAN_STAGING_ADMIN_READONLY_DATABASE_URL",)
        )
    if admin_http_enabled:
        _require_nonempty(environment, ("XIEWENXIAN_ADMIN_SESSION_SECRET",))
    if livekit_enabled:
        _require_nonempty(
            environment,
            (
                "XIEWENXIAN_CALIBRATION_LIVEKIT_URL",
                "XIEWENXIAN_CALIBRATION_LIVEKIT_API_KEY",
                "XIEWENXIAN_CALIBRATION_LIVEKIT_API_SECRET",
            ),
        )

    return RuntimeConfiguration(
        mode=mode,
        app_env=app_env,
        log_level=log_level,
        providers_enabled=providers_enabled,
        line_integration_enabled=line_enabled,
        database_enabled=database_enabled,
        admin_database_enabled=admin_database_enabled,
        admin_http_enabled=admin_http_enabled,
        livekit_enabled=livekit_enabled,
        sandbox_mode=sandbox_mode,
        kill_switch=kill_switch,
        defaults=defaults,
    )


def _validate_duplex_invariants(defaults: RuntimeDefaults) -> None:
    if defaults.voice_input_encoding != "pcm_s16le":
        raise ConfigurationError("VOICE_INPUT_ENCODING must remain pcm_s16le")
    if defaults.voice_input_channels != 1 or defaults.minimax_channels != 1:
        raise ConfigurationError("Phase 3C audio must remain mono")
    if defaults.minimax_output_format != "mp3":
        raise ConfigurationError("MINIMAX_OUTPUT_FORMAT must match the verified mp3 contract")
    if defaults.tts_session_strategy != "one_session_per_generation":
        raise ConfigurationError("TTS_SESSION_STRATEGY must be one_session_per_generation")
    if not defaults.generation_guard_enabled:
        raise ConfigurationError("GENERATION_GUARD_ENABLED cannot be disabled")
    if defaults.stale_generation_policy != "discard":
        raise ConfigurationError("STALE_GENERATION_POLICY must be discard")
    if defaults.enable_audio_dump:
        raise ConfigurationError("audio dumps are forbidden in Phase 3C")
    if not (
        defaults.text_chunk_min_chars
        < defaults.text_chunk_preferred_chars
        < defaults.text_chunk_max_chars
    ):
        raise ConfigurationError("text chunk sizes must be strictly increasing")
    numeric_values = (
        defaults.min_overlap_ms,
        defaults.interruption_confirmation_ms,
        defaults.tts_max_pending_audio_ms,
        defaults.input_queue_max_ms,
    )
    if not all(math.isfinite(float(value)) and value > 0 for value in numeric_values):
        raise ConfigurationError("duplex timing limits must be finite and positive")


__all__ = [
    "ENVIRONMENT_CONTRACT",
    "PUBLIC_BROWSER_ENV_NAMES",
    "SECRET_ENV_NAMES",
    "ConfigurationError",
    "EnvironmentVariableContract",
    "RuntimeConfiguration",
    "RuntimeDefaults",
    "RuntimeMode",
    "ValueClass",
    "load_runtime_configuration",
]
