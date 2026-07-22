"""Fail-closed LINE ID-token verification and Phase 3B identity mapping boundary.

This module defines the server-side contract for LINE's official ID-token verification endpoint.
It deliberately performs no network I/O itself: a separately configured transport must POST the
opaque ID token and expected Channel ID to LINE. Client-decoded claims are never accepted.
"""

from __future__ import annotations

import asyncio
import re
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Protocol

from duplex_voice.calibration.identity import (
    XIEWENXIAN_NAMESPACES,
    CalibrationPermission,
    CalibrationRole,
    OwnerCalibrationPolicy,
    load_owner_calibration_policy,
)
from duplex_voice.calibration.identity_mapping import (
    IdentityMappingError,
    PrincipalIdentity,
    PrincipalKind,
    SourceSystem,
    VerifiedIdentityAssertion,
    map_verified_identity,
)
from duplex_voice.calibration.identity_verifier import IdentityVerifier, OpaqueCredential

LINE_ID_TOKEN_VERIFY_ENDPOINT = "https://api.line.me/oauth2/v2.1/verify"
LINE_ID_TOKEN_ISSUER = "https://access.line.me"
_CHANNEL_ID = re.compile(r"^[0-9]{8,20}$")
_LIFF_ID = re.compile(r"^[0-9]{8,20}-[A-Za-z0-9_-]{4,64}$")

type SafeEvent = dict[str, str | bool]
type EventSink = Callable[[SafeEvent], None]


class LineIdentityVerificationError(ValueError):
    """Safe, token-free verification failure."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class LineIdentitySettings:
    """Public verification settings bound to the Xie Wenxian staging tenant."""

    channel_id: str
    liff_id: str
    policy: OwnerCalibrationPolicy = field(repr=False)
    issuer: str = LINE_ID_TOKEN_ISSUER
    tenant_id: str = XIEWENXIAN_NAMESPACES.tenant_id
    persona_id: str = XIEWENXIAN_NAMESPACES.persona_id
    timeout_s: float = 2.0

    def __post_init__(self) -> None:
        if not _CHANNEL_ID.fullmatch(self.channel_id):
            raise LineIdentityVerificationError("invalid_channel_id_config")
        if not _LIFF_ID.fullmatch(self.liff_id):
            raise LineIdentityVerificationError("invalid_liff_id_config")
        if self.issuer != LINE_ID_TOKEN_ISSUER:
            raise LineIdentityVerificationError("issuer_config_mismatch")
        if self.tenant_id != XIEWENXIAN_NAMESPACES.tenant_id:
            raise LineIdentityVerificationError("tenant_mismatch")
        if self.persona_id != XIEWENXIAN_NAMESPACES.persona_id:
            raise LineIdentityVerificationError("persona_mismatch")
        if self.policy.namespaces != XIEWENXIAN_NAMESPACES:
            raise LineIdentityVerificationError("policy_namespace_mismatch")
        if not self.policy.enabled:
            raise LineIdentityVerificationError("calibration_disabled")
        if self.policy.kill_switch:
            raise LineIdentityVerificationError("kill_switch_active")
        if not self.policy.sandbox_mode:
            raise LineIdentityVerificationError("sandbox_required")
        if not 0 < self.timeout_s <= 10:
            raise LineIdentityVerificationError("invalid_timeout_config")


def load_line_identity_settings(environment: Mapping[str, str]) -> LineIdentitySettings:
    """Load public settings only when the explicit staging identity flag is enabled."""

    if environment.get("LIFF_IDENTITY_ENABLED", "false").strip().casefold() != "true":
        raise LineIdentityVerificationError("identity_disabled")
    if environment.get("APP_ENV", "").strip().casefold() != "staging":
        raise LineIdentityVerificationError("staging_environment_required")
    if environment.get("XIEWENXIAN_CALIBRATION_SANDBOX_MODE", "true").strip().casefold() != "true":
        raise LineIdentityVerificationError("sandbox_required")

    channel_id = environment.get("XIEWENXIAN_CALIBRATION_LINE_CHANNEL_ID", "").strip()
    liff_id = environment.get("XIEWENXIAN_CALIBRATION_LIFF_ID", "").strip()
    if not channel_id or not liff_id:
        raise LineIdentityVerificationError("identity_public_config_missing")

    try:
        policy = load_owner_calibration_policy(environment)
    except ValueError:
        raise LineIdentityVerificationError("invalid_calibration_policy") from None

    return LineIdentitySettings(
        channel_id=channel_id,
        liff_id=liff_id,
        issuer=environment.get(
            "XIEWENXIAN_CALIBRATION_LINE_ISSUER", LINE_ID_TOKEN_ISSUER
        ).strip(),
        policy=policy,
    )


@dataclass(frozen=True, slots=True)
class LineIdTokenVerifyRequest:
    """Form request contract for LINE Login v2.1 Verify ID token."""

    client_id: str
    id_token: str = field(repr=False)
    endpoint: str = LINE_ID_TOKEN_VERIFY_ENDPOINT

    def __post_init__(self) -> None:
        if self.endpoint != LINE_ID_TOKEN_VERIFY_ENDPOINT:
            raise LineIdentityVerificationError("verification_endpoint_mismatch")
        if not _CHANNEL_ID.fullmatch(self.client_id):
            raise LineIdentityVerificationError("invalid_channel_id_config")
        if not 16 <= len(self.id_token) <= 8_192 or self.id_token.count(".") != 2:
            raise LineIdentityVerificationError("malformed_id_token")

    def safe_summary(self) -> dict[str, str]:
        return {"endpoint": self.endpoint, "client_id": self.client_id}


class LineIdTokenVerifyTransport(Protocol):
    """Replaceable transport that calls LINE's official verification endpoint."""

    async def verify_id_token(
        self, request: LineIdTokenVerifyRequest
    ) -> Mapping[str, object]: ...


class LineIdTokenVerifier(IdentityVerifier):
    """Validate the trusted LINE response before producing a verified assertion."""

    def __init__(
        self,
        *,
        settings: LineIdentitySettings,
        transport: LineIdTokenVerifyTransport,
        monotonic_time: Callable[[], float] = time.time,
        event_sink: EventSink | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport
        self._time = monotonic_time
        self._event_sink = event_sink

    async def verify(self, credential: OpaqueCredential) -> VerifiedIdentityAssertion:
        try:
            request = LineIdTokenVerifyRequest(
                client_id=self._settings.channel_id,
                id_token=credential.value,
            )
        except LineIdentityVerificationError as exc:
            self._emit("line_identity_rejected", exc.code)
            raise

        self._emit("line_identity_verification_started", "verification_started")
        try:
            response = await asyncio.wait_for(
                self._transport.verify_id_token(request),
                timeout=self._settings.timeout_s,
            )
        except TimeoutError:
            self._emit("line_identity_rejected", "verification_timeout")
            raise LineIdentityVerificationError("verification_timeout") from None
        except Exception:
            self._emit("line_identity_rejected", "verification_upstream_error")
            raise LineIdentityVerificationError("verification_upstream_error") from None

        try:
            assertion = self._validate_response(response)
        except LineIdentityVerificationError as exc:
            self._emit("line_identity_rejected", exc.code)
            raise
        self._emit("line_identity_verified", "verified")
        return assertion

    def _validate_response(
        self, response: Mapping[str, object]
    ) -> VerifiedIdentityAssertion:
        if any(name in response for name in ("name", "picture", "email")):
            raise LineIdentityVerificationError("unexpected_profile_claims")

        issuer = response.get("iss")
        audience = response.get("aud")
        expires_at = response.get("exp")
        subject = response.get("sub")
        if issuer != self._settings.issuer:
            raise LineIdentityVerificationError("wrong_issuer")
        if audience != self._settings.channel_id:
            raise LineIdentityVerificationError("wrong_audience")
        if isinstance(expires_at, bool) or not isinstance(expires_at, int):
            raise LineIdentityVerificationError("invalid_expiry")
        if expires_at <= int(self._time()):
            raise LineIdentityVerificationError("expired_token")
        if not isinstance(subject, str) or not subject:
            raise LineIdentityVerificationError("missing_subject")

        try:
            return VerifiedIdentityAssertion(
                source_system=SourceSystem.LINE,
                external_user_id=subject,
                principal_kind=PrincipalKind.TECHNICAL_TESTER,
                verified=True,
                provider_audience=self._settings.channel_id,
            )
        except IdentityMappingError as exc:
            raise LineIdentityVerificationError("invalid_subject") from exc

    def _emit(self, event: str, code: str) -> None:
        if self._event_sink is not None:
            self._event_sink(
                {
                    "event": event,
                    "code": code,
                    "provider": "line",
                    "contains_identity_value": False,
                }
            )


@dataclass(frozen=True, slots=True)
class LineIdentityOutcome:
    verified: bool
    code: str
    principal: PrincipalIdentity | None = None

    def safe_response(self) -> dict[str, object]:
        response: dict[str, object] = {"verified": self.verified, "code": self.code}
        if self.principal is not None:
            response["principal"] = self.principal.safe_summary()
        return response


class LineIdentityBoundary:
    """Verify and immediately map the raw subject into the existing Phase 3B identity."""

    def __init__(self, *, settings: LineIdentitySettings, verifier: IdentityVerifier) -> None:
        self._settings = settings
        self._verifier = verifier

    async def activate(self, raw_id_token: str) -> LineIdentityOutcome:
        try:
            assertion = await self._verifier.verify(OpaqueCredential(raw_id_token))
            if assertion.source_system is not SourceSystem.LINE:
                raise LineIdentityVerificationError("wrong_identity_provider")
            if assertion.provider_audience != self._settings.channel_id:
                raise LineIdentityVerificationError("wrong_audience_binding")
            decision = self._settings.policy.authorize(
                assertion.external_user_id,
                CalibrationPermission.INTERACT,
            )
            if not decision.allowed:
                raise LineIdentityVerificationError(decision.reason)
            principal_kind = _principal_kind_for_role(decision.role)
            authorized_assertion = VerifiedIdentityAssertion(
                source_system=assertion.source_system,
                external_user_id=assertion.external_user_id,
                principal_kind=principal_kind,
                verified=assertion.verified,
                provider_audience=assertion.provider_audience,
            )
            principal = map_verified_identity(
                authorized_assertion,
                tenant_id=self._settings.tenant_id,
            )
        except LineIdentityVerificationError as exc:
            return LineIdentityOutcome(False, exc.code)
        except (IdentityMappingError, ValueError):
            return LineIdentityOutcome(False, "identity_rejected")
        return LineIdentityOutcome(True, "verified", principal)


def _principal_kind_for_role(role: CalibrationRole) -> PrincipalKind:
    mapping = {
        CalibrationRole.OWNER: PrincipalKind.OWNER,
        CalibrationRole.GOVERNOR: PrincipalKind.GOVERNOR,
        CalibrationRole.TECHNICAL_TESTER: PrincipalKind.TECHNICAL_TESTER,
    }
    try:
        return mapping[role]
    except KeyError:
        raise LineIdentityVerificationError("line_user_not_allowlisted") from None


__all__ = [
    "LINE_ID_TOKEN_ISSUER",
    "LINE_ID_TOKEN_VERIFY_ENDPOINT",
    "LineIdTokenVerifier",
    "LineIdTokenVerifyRequest",
    "LineIdTokenVerifyTransport",
    "LineIdentityBoundary",
    "LineIdentityOutcome",
    "LineIdentitySettings",
    "LineIdentityVerificationError",
    "load_line_identity_settings",
]
