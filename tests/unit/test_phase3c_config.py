from __future__ import annotations

import json
from pathlib import Path

import pytest

from duplex_voice.config import (
    ENVIRONMENT_CONTRACT,
    PUBLIC_BROWSER_ENV_NAMES,
    SECRET_ENV_NAMES,
    ConfigurationError,
    RuntimeMode,
    ValueClass,
    load_runtime_configuration,
)


def test_offline_defaults_load_without_credentials_and_keep_kill_switch() -> None:
    config = load_runtime_configuration({})

    assert config.mode is RuntimeMode.OFFLINE_HARDENING
    assert config.app_env == "development"
    assert config.kill_switch
    assert config.sandbox_mode
    assert not config.providers_enabled
    assert config.defaults.voice_input_sample_rate == 16_000
    assert config.defaults.minimax_sample_rate == 24_000


@pytest.mark.parametrize(
    "environment",
    [
        {"APP_ENV": "production"},
        {"GENERATION_GUARD_ENABLED": "false"},
        {"TTS_SESSION_STRATEGY": "connection_pool"},
        {"STALE_GENERATION_POLICY": "play"},
        {"MINIMAX_OUTPUT_FORMAT": "pcm"},
        {"VOICE_INPUT_CHANNELS": "2"},
        {"ENABLE_AUDIO_DUMP": "true"},
        {"XIEWENXIAN_CALIBRATION_SANDBOX_MODE": "false"},
        {"XIEWENXIAN_CALIBRATION_KILL_SWITCH": "false"},
    ],
)
def test_offline_configuration_rejects_boundary_weakening(
    environment: dict[str, str],
) -> None:
    with pytest.raises(ConfigurationError):
        load_runtime_configuration(environment)


@pytest.mark.parametrize(
    "flag",
    [
        "EXTERNAL_PROVIDERS_ENABLED",
        "LINE_INTEGRATION_ENABLED",
        "DATABASE_ENABLED",
        "ADMIN_DATABASE_ENABLED",
        "ADMIN_HTTP_ENABLED",
        "LIVEKIT_ENABLED",
    ],
)
def test_offline_configuration_rejects_every_external_integration(flag: str) -> None:
    with pytest.raises(ConfigurationError, match=flag):
        load_runtime_configuration({flag: "true"})


def test_staging_provider_activation_requires_all_provider_slots() -> None:
    with pytest.raises(ConfigurationError) as exc_info:
        load_runtime_configuration(
            {
                "APP_ENV": "staging",
                "EXTERNAL_PROVIDERS_ENABLED": "true",
            },
            mode=RuntimeMode.STAGING_INTEGRATION,
        )

    message = str(exc_info.value)
    assert "MINIMAX_API_KEY" in message
    assert "XIEWENXIAN_CALIBRATION_MINIMAX_VOICE_ID" in message
    assert "XIEWENXIAN_STT_API_KEY" in message
    assert "XIEWENXIAN_LLM_API_KEY" in message


def test_staging_provider_contract_can_validate_without_contacting_provider() -> None:
    config = load_runtime_configuration(
        {
            "APP_ENV": "staging",
            "EXTERNAL_PROVIDERS_ENABLED": "true",
            "MINIMAX_API_KEY": "synthetic-minimax-key",
            "MINIMAX_MODEL": "synthetic-model",
            "XIEWENXIAN_CALIBRATION_MINIMAX_VOICE_ID": "synthetic-voice",
            "XIEWENXIAN_STT_API_KEY": "synthetic-stt-key",
            "XIEWENXIAN_STT_MODEL": "synthetic-stt-model",
            "XIEWENXIAN_LLM_API_KEY": "synthetic-llm-key",
            "XIEWENXIAN_LLM_MODEL": "synthetic-llm-model",
        },
        mode=RuntimeMode.STAGING_INTEGRATION,
    )

    rendered = json.dumps(config.redacted_snapshot())
    assert config.providers_enabled
    assert "synthetic" not in rendered
    assert "synthetic-voice" not in rendered
    assert "synthetic-minimax-key" not in rendered


def test_secret_contract_never_exposes_a_secret_to_browser() -> None:
    assert SECRET_ENV_NAMES.isdisjoint(PUBLIC_BROWSER_ENV_NAMES)
    assert all(not name.startswith("VITE_") for name in SECRET_ENV_NAMES)
    assert all(
        item.value_class is ValueClass.PUBLIC_CONFIG
        for item in ENVIRONMENT_CONTRACT
        if item.consumer == "browser"
    )


def test_env_example_and_machine_readable_contract_have_the_same_names() -> None:
    example_names = {
        line.split("=", maxsplit=1)[0]
        for line in Path(".env.example").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    }
    contract_names = {item.name for item in ENVIRONMENT_CONTRACT}

    assert len(contract_names) == len(ENVIRONMENT_CONTRACT)
    assert example_names == contract_names


def test_invalid_boolean_and_integer_are_rejected_safely() -> None:
    with pytest.raises(ConfigurationError, match="boolean"):
        load_runtime_configuration({"ENABLE_INTERRUPTION": "sometimes"})
    with pytest.raises(ConfigurationError, match="integer"):
        load_runtime_configuration({"VOICE_INPUT_FRAME_MS": "fast"})


def test_text_chunk_limits_must_remain_strictly_increasing() -> None:
    with pytest.raises(ConfigurationError, match="strictly increasing"):
        load_runtime_configuration(
            {
                "TEXT_CHUNK_MIN_CHARS": "20",
                "TEXT_CHUNK_PREFERRED_CHARS": "10",
                "TEXT_CHUNK_MAX_CHARS": "30",
            }
        )
