"""Verified external identity to staging-principal mapping.

The mapper never verifies LINE tokens or partner credentials itself.  A future adapter must
produce a verified assertion first.  This keeps Phase 3B provider-free and makes accidental trust
of client-provided IDs impossible.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import StrEnum

from duplex_voice.calibration.identity import XIEWENXIAN_NAMESPACES

_SAFE_EXTERNAL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@-]{0,127}$")


class IdentityMappingError(ValueError):
    """Raised when an external identity cannot enter the staging boundary."""


class SourceSystem(StrEnum):
    LINE = "line"
    PARTNER = "partner"
    SYNTHETIC = "synthetic"


class PrincipalKind(StrEnum):
    OWNER = "owner"
    STUDENT = "student"
    GOVERNOR = "governor"
    TECHNICAL_TESTER = "technical_tester"


@dataclass(frozen=True, slots=True)
class VerifiedIdentityAssertion:
    source_system: SourceSystem
    external_user_id: str
    principal_kind: PrincipalKind
    verified: bool

    def __post_init__(self) -> None:
        if not _SAFE_EXTERNAL_ID.fullmatch(self.external_user_id):
            raise IdentityMappingError("external user ID must be a bounded opaque identifier")
        if (
            self.source_system is SourceSystem.SYNTHETIC
            and not self.external_user_id.startswith("synthetic-")
        ):
            raise IdentityMappingError("synthetic identity must use the synthetic prefix")


@dataclass(frozen=True, slots=True)
class PrincipalIdentity:
    tenant_id: str
    source_system: SourceSystem
    principal_kind: PrincipalKind
    effective_user_id: str
    external_user_id_hash: str

    def safe_summary(self) -> dict[str, str]:
        return {
            "tenant_id": self.tenant_id,
            "source_system": self.source_system.value,
            "principal_kind": self.principal_kind.value,
            "principal_fingerprint": self.external_user_id_hash[:12],
        }


def map_verified_identity(
    assertion: VerifiedIdentityAssertion,
    *,
    tenant_id: str = XIEWENXIAN_NAMESPACES.tenant_id,
) -> PrincipalIdentity:
    """Create a stable, data-minimized effective ID from a verified assertion."""
    if tenant_id != XIEWENXIAN_NAMESPACES.tenant_id:
        raise IdentityMappingError("Phase 3B accepts only the Xie Wenxian staging tenant")
    if assertion.verified is not True:
        raise IdentityMappingError("unverified external identity is denied")

    digest = hashlib.sha256(
        f"{assertion.source_system.value}\0{assertion.external_user_id}".encode()
    ).hexdigest()
    effective_user_id = f"{tenant_id}:{assertion.source_system.value}:{digest}"
    return PrincipalIdentity(
        tenant_id=tenant_id,
        source_system=assertion.source_system,
        principal_kind=assertion.principal_kind,
        effective_user_id=effective_user_id,
        external_user_id_hash=digest,
    )


__all__ = [
    "IdentityMappingError",
    "PrincipalIdentity",
    "PrincipalKind",
    "SourceSystem",
    "VerifiedIdentityAssertion",
    "map_verified_identity",
]
