from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from dataclasses import dataclass

import pytest

from duplex_voice.calibration.identity import XIEWENXIAN_NAMESPACES
from duplex_voice.calibration.identity_verifier import OpaqueCredential
from duplex_voice.calibration.line_identity import (
    LINE_ID_TOKEN_ISSUER,
    LINE_ID_TOKEN_VERIFY_ENDPOINT,
    LineIdentityBoundary,
    LineIdentitySettings,
    LineIdentityVerificationError,
    LineIdTokenVerifier,
    LineIdTokenVerifyRequest,
    load_line_identity_settings,
)

SYNTHETIC_TOKEN = "synthetic-header.synthetic-payload.synthetic-signature"
SYNTHETIC_SUBJECT = "U0123456789abcdef0123456789abcdef"
CHANNEL_ID = "1234567890"
LIFF_ID = "2010776532-YooRYUEg"
NOW = 1_800_000_000


@dataclass
class FakeLineTransport:
    response: Mapping[str, object] | None = None
    delay_s: float = 0
    error: Exception | None = None
    request: LineIdTokenVerifyRequest | None = None

    async def verify_id_token(
        self, request: LineIdTokenVerifyRequest
    ) -> Mapping[str, object]:
        self.request = request
        if self.delay_s:
            await asyncio.sleep(self.delay_s)
        if self.error is not None:
            raise self.error
        if self.response is None:
            raise RuntimeError("fake response missing")
        return self.response


def _settings(**overrides: object) -> LineIdentitySettings:
    values: dict[str, object] = {
        "channel_id": CHANNEL_ID,
        "liff_id": LIFF_ID,
        "timeout_s": 0.05,
    }
    values.update(overrides)
    return LineIdentitySettings(**values)  # type: ignore[arg-type]


def _valid_response(**overrides: object) -> dict[str, object]:
    response: dict[str, object] = {
        "iss": LINE_ID_TOKEN_ISSUER,
        "aud": CHANNEL_ID,
        "exp": NOW + 3_600,
        "iat": NOW,
        "sub": SYNTHETIC_SUBJECT,
    }
    response.update(overrides)
    return response


def _verifier(
    transport: FakeLineTransport,
    *,
    events: list[dict[str, str | bool]] | None = None,
) -> LineIdTokenVerifier:
    return LineIdTokenVerifier(
        settings=_settings(),
        transport=transport,
        monotonic_time=lambda: NOW,
        event_sink=None if events is None else events.append,
    )


@pytest.mark.asyncio
async def test_valid_official_verification_response_maps_through_phase3b() -> None:
    transport = FakeLineTransport(_valid_response())
    settings = _settings()
    boundary = LineIdentityBoundary(
        settings=settings,
        verifier=LineIdTokenVerifier(
            settings=settings,
            transport=transport,
            monotonic_time=lambda: NOW,
        ),
    )

    outcome = await boundary.activate(SYNTHETIC_TOKEN)

    assert outcome.verified is True
    assert outcome.principal is not None
    assert outcome.principal.tenant_id == XIEWENXIAN_NAMESPACES.tenant_id
    assert outcome.principal.effective_user_id.startswith("xie_wenxian:line:")
    assert SYNTHETIC_SUBJECT not in json.dumps(outcome.safe_response())
    assert SYNTHETIC_TOKEN not in json.dumps(outcome.safe_response())
    assert transport.request is not None
    assert transport.request.endpoint == LINE_ID_TOKEN_VERIFY_ENDPOINT
    assert transport.request.client_id == CHANNEL_ID


@pytest.mark.asyncio
@pytest.mark.parametrize("token", ["", "not-a-jwt", "a.b", "a.b.c.d"])
async def test_missing_or_malformed_tokens_fail_closed(token: str) -> None:
    transport = FakeLineTransport(_valid_response())
    boundary = LineIdentityBoundary(settings=_settings(), verifier=_verifier(transport))

    outcome = await boundary.activate(token)

    assert outcome.verified is False
    assert outcome.code in {"identity_rejected", "malformed_id_token"}
    assert transport.request is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"exp": NOW - 1}, "expired_token"),
        ({"aud": "9999999999"}, "wrong_audience"),
        ({"iss": "https://issuer.invalid"}, "wrong_issuer"),
        ({"sub": ""}, "missing_subject"),
        ({"sub": None}, "missing_subject"),
        ({"name": "must-not-be-requested"}, "unexpected_profile_claims"),
    ],
)
async def test_invalid_verified_claims_fail_closed(
    overrides: dict[str, object], code: str
) -> None:
    transport = FakeLineTransport(_valid_response(**overrides))
    boundary = LineIdentityBoundary(settings=_settings(), verifier=_verifier(transport))

    outcome = await boundary.activate(SYNTHETIC_TOKEN)

    assert outcome == type(outcome)(False, code)


@pytest.mark.asyncio
async def test_upstream_timeout_and_error_are_redacted() -> None:
    timeout_boundary = LineIdentityBoundary(
        settings=_settings(),
        verifier=_verifier(FakeLineTransport(_valid_response(), delay_s=0.2)),
    )
    error_boundary = LineIdentityBoundary(
        settings=_settings(),
        verifier=_verifier(FakeLineTransport(error=RuntimeError(SYNTHETIC_TOKEN))),
    )

    timeout = await timeout_boundary.activate(SYNTHETIC_TOKEN)
    upstream_error = await error_boundary.activate(SYNTHETIC_TOKEN)

    assert timeout.code == "verification_timeout"
    assert upstream_error.code == "verification_upstream_error"
    assert SYNTHETIC_TOKEN not in json.dumps(upstream_error.safe_response())


def test_tenant_and_persona_mismatch_fail_during_configuration() -> None:
    with pytest.raises(LineIdentityVerificationError, match="tenant_mismatch"):
        _settings(tenant_id="other_tenant")
    with pytest.raises(LineIdentityVerificationError, match="persona_mismatch"):
        _settings(persona_id="other_persona")


@pytest.mark.asyncio
async def test_raw_token_and_subject_are_absent_from_repr_events_and_response() -> None:
    events: list[dict[str, str | bool]] = []
    verifier = _verifier(FakeLineTransport(_valid_response()), events=events)
    assertion = await verifier.verify(OpaqueCredential(SYNTHETIC_TOKEN))
    boundary = LineIdentityBoundary(settings=_settings(), verifier=verifier)
    outcome = await boundary.activate(SYNTHETIC_TOKEN)
    combined = repr(assertion) + json.dumps(events) + json.dumps(outcome.safe_response())

    assert SYNTHETIC_TOKEN not in combined
    assert SYNTHETIC_SUBJECT not in combined


def test_identity_configuration_is_staging_only_and_fail_closed() -> None:
    base = {
        "APP_ENV": "staging",
        "LIFF_IDENTITY_ENABLED": "true",
        "XIEWENXIAN_CALIBRATION_SANDBOX_MODE": "true",
        "XIEWENXIAN_CALIBRATION_LINE_CHANNEL_ID": CHANNEL_ID,
        "XIEWENXIAN_CALIBRATION_LIFF_ID": LIFF_ID,
    }
    assert load_line_identity_settings(base).liff_id == LIFF_ID

    for missing in (
        "LIFF_IDENTITY_ENABLED",
        "XIEWENXIAN_CALIBRATION_LINE_CHANNEL_ID",
        "XIEWENXIAN_CALIBRATION_LIFF_ID",
    ):
        environment = dict(base)
        environment.pop(missing)
        with pytest.raises(LineIdentityVerificationError):
            load_line_identity_settings(environment)

    with pytest.raises(LineIdentityVerificationError, match="staging_environment_required"):
        load_line_identity_settings({**base, "APP_ENV": "production"})
