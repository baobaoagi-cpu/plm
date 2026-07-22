from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

import pytest

from duplex_voice.config import ConfigurationError
from duplex_voice.staging_server import application, load_staging_server_settings


def _request(method: str, path: str) -> tuple[str, dict[str, str], bytes]:
    captured_status = ""
    captured_headers: list[tuple[str, str]] = []

    def start_response(status: str, headers: list[tuple[str, str]]) -> object:
        nonlocal captured_status, captured_headers
        captured_status = status
        captured_headers = headers
        return None

    chunks = application(
        {"REQUEST_METHOD": method, "PATH_INFO": path},
        start_response,
    )
    return captured_status, dict(captured_headers), b"".join(chunks)


def test_health_endpoint_is_minimal_staging_only_and_not_cacheable() -> None:
    status, headers, body = _request("GET", "/healthz")

    assert status == "200 OK"
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert headers["Cache-Control"] == "no-store"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert int(headers["Content-Length"]) == len(body)
    assert json.loads(body) == {
        "environment": "staging",
        "external_integrations_enabled": False,
        "production_ready": False,
        "purpose": "deployment_readiness",
        "service": "plm-staging-deployment-shell",
        "status": "ok",
    }


def test_head_health_endpoint_has_no_body() -> None:
    status, headers, body = _request("HEAD", "/healthz")

    assert status == "200 OK"
    assert int(headers["Content-Length"]) > 0
    assert body == b""


@pytest.mark.parametrize(
    ("method", "path", "expected_status"),
    (("POST", "/healthz", "405 Method Not Allowed"), ("GET", "/missing", "404 Not Found")),
)
def test_staging_shell_rejects_unsupported_requests(
    method: str, path: str, expected_status: str
) -> None:
    status, _, _ = _request(method, path)
    assert status == expected_status


def test_settings_bind_railway_port_and_keep_integrations_disabled() -> None:
    settings = load_staging_server_settings(
        {
            "APP_ENV": "staging",
            "PORT": "9123",
            "RAILWAY_ENVIRONMENT_NAME": "staging",
        }
    )

    assert settings.host == "0.0.0.0"
    assert settings.port == 9123
    assert settings.runtime.providers_enabled is False
    assert settings.runtime.line_integration_enabled is False
    assert settings.runtime.liff_identity_enabled is False
    assert settings.runtime.database_enabled is False
    assert settings.runtime.livekit_enabled is False
    assert settings.runtime.sandbox_mode is True
    assert settings.runtime.kill_switch is True


@pytest.mark.parametrize(
    "environment",
    (
        {"APP_ENV": "production"},
        {"RAILWAY_ENVIRONMENT_NAME": "production"},
        {"EXTERNAL_PROVIDERS_ENABLED": "true"},
        {"LINE_INTEGRATION_ENABLED": "true"},
        {"LIFF_IDENTITY_ENABLED": "true"},
        {"DATABASE_ENABLED": "true"},
        {"LIVEKIT_ENABLED": "true"},
        {"XIEWENXIAN_CALIBRATION_KILL_SWITCH": "false"},
        {"XIEWENXIAN_CALIBRATION_SANDBOX_MODE": "false"},
        {"PORT": "invalid"},
        {"PORT": "65536"},
    ),
)
def test_settings_fail_closed_outside_authorized_staging_shell(
    environment: dict[str, str],
) -> None:
    with pytest.raises(ConfigurationError):
        load_staging_server_settings(environment)


def test_railway_config_enables_only_staging_deployment() -> None:
    config: dict[str, Any]
    with Path("railway.toml").open("rb") as file:
        config = tomllib.load(file)

    assert config["build"] == {"builder": "RAILPACK"}
    assert "deploy" not in config
    assert set(config["environments"]) == {"staging"}
    staging_deploy = config["environments"]["staging"]["deploy"]
    assert staging_deploy["startCommand"] == "uv run python -m duplex_voice.staging_server"
    assert staging_deploy["healthcheckPath"] == "/healthz"
    assert staging_deploy["healthcheckTimeout"] == 60
    assert staging_deploy["restartPolicyType"] == "ON_FAILURE"
    assert staging_deploy["restartPolicyMaxRetries"] == 3
