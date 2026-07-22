"""Fail-closed HTTP shell for Railway staging deployment verification only."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from os import environ
from typing import Any, Final
from urllib.parse import urlsplit
from wsgiref.simple_server import make_server

from duplex_voice.config import (
    ConfigurationError,
    RuntimeConfiguration,
    RuntimeMode,
    load_runtime_configuration,
)

type WSGIEnvironment = dict[str, Any]
type StartResponse = Callable[[str, list[tuple[str, str]]], object]

_SERVICE_NAME: Final = "plm-staging-deployment-shell"
_HEALTH_BODY: Final = {
    "status": "ok",
    "service": _SERVICE_NAME,
    "environment": "staging",
    "purpose": "deployment_readiness",
    "production_ready": False,
    "external_integrations_enabled": False,
}
_ROOT_BODY: Final = {
    "service": _SERVICE_NAME,
    "status": "staging_only",
    "health": "/healthz",
    "production_ready": False,
}


@dataclass(frozen=True, slots=True)
class StagingServerSettings:
    """Validated network and safety settings for the staging-only shell."""

    host: str
    port: int
    runtime: RuntimeConfiguration


def load_staging_server_settings(
    environment: Mapping[str, str] = environ,
) -> StagingServerSettings:
    """Load settings while refusing production and every external integration."""

    railway_environment = environment.get("RAILWAY_ENVIRONMENT_NAME")
    if railway_environment is not None and railway_environment.strip().casefold() != "staging":
        raise ConfigurationError(
            "the deployment shell may run only in the Railway staging environment"
        )

    isolated_environment = dict(environment)
    isolated_environment.setdefault("APP_ENV", "staging")
    if isolated_environment["APP_ENV"].strip().casefold() != "staging":
        raise ConfigurationError("the deployment shell requires APP_ENV=staging")

    runtime = load_runtime_configuration(
        isolated_environment,
        mode=RuntimeMode.OFFLINE_HARDENING,
    )

    raw_port = environment.get("PORT", "8080").strip()
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise ConfigurationError("PORT must be an integer") from exc
    if not 1 <= port <= 65_535:
        raise ConfigurationError("PORT must be between 1 and 65535")

    return StagingServerSettings(host="0.0.0.0", port=port, runtime=runtime)


def _json_response(
    start_response: StartResponse,
    *,
    status: str,
    body: Mapping[str, object],
    include_body: bool,
) -> list[bytes]:
    payload = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(payload))),
        ("Cache-Control", "no-store"),
        ("X-Content-Type-Options", "nosniff"),
    ]
    start_response(status, headers)
    return [payload] if include_body else [b""]


def application(environ: WSGIEnvironment, start_response: StartResponse) -> list[bytes]:
    """Serve only a public landing response and a dependency-free health check."""

    method = str(environ.get("REQUEST_METHOD", "GET")).upper()
    path = urlsplit(str(environ.get("PATH_INFO", "/"))).path
    if method not in {"GET", "HEAD"}:
        return _json_response(
            start_response,
            status="405 Method Not Allowed",
            body={"error": "method_not_allowed"},
            include_body=method != "HEAD",
        )
    if path == "/healthz":
        return _json_response(
            start_response,
            status="200 OK",
            body=_HEALTH_BODY,
            include_body=method == "GET",
        )
    if path == "/":
        return _json_response(
            start_response,
            status="200 OK",
            body=_ROOT_BODY,
            include_body=method == "GET",
        )
    return _json_response(
        start_response,
        status="404 Not Found",
        body={"error": "not_found"},
        include_body=method == "GET",
    )


def main() -> None:
    """Run the staging-only WSGI server on Railway's assigned port."""

    settings = load_staging_server_settings()
    startup_event = {
        "event": "staging_health_server_started",
        "host": settings.host,
        "port": settings.port,
        "external_integrations_enabled": False,
        "production_ready": False,
    }
    print(json.dumps(startup_event, sort_keys=True), flush=True)
    with make_server(settings.host, settings.port, application) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
