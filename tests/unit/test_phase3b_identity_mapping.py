from __future__ import annotations

import pytest

from duplex_voice.calibration.identity_mapping import (
    IdentityMappingError,
    PrincipalKind,
    SourceSystem,
    VerifiedIdentityAssertion,
    map_verified_identity,
)


def _assertion(
    external_user_id: str = "synthetic-student-a",
    *,
    source_system: SourceSystem = SourceSystem.SYNTHETIC,
    principal_kind: PrincipalKind = PrincipalKind.STUDENT,
    verified: bool = True,
) -> VerifiedIdentityAssertion:
    return VerifiedIdentityAssertion(
        source_system=source_system,
        external_user_id=external_user_id,
        principal_kind=principal_kind,
        verified=verified,
    )


def test_verified_identity_maps_to_stable_effective_user_id() -> None:
    first = map_verified_identity(_assertion())
    second = map_verified_identity(_assertion())

    assert first == second
    assert first.tenant_id == "xie_wenxian"
    assert first.effective_user_id.startswith("xie_wenxian:synthetic:")
    assert len(first.external_user_id_hash) == 64


def test_effective_user_id_and_safe_summary_never_expose_external_id() -> None:
    external_id = "U-synthetic-owner-private"
    principal = map_verified_identity(
        _assertion(
            external_id,
            source_system=SourceSystem.LINE,
            principal_kind=PrincipalKind.OWNER,
        )
    )

    assert external_id not in principal.effective_user_id
    assert external_id not in "".join(principal.safe_summary().values())
    assert set(principal.safe_summary()) == {
        "tenant_id",
        "source_system",
        "principal_kind",
        "principal_fingerprint",
    }


def test_source_system_is_part_of_identity_boundary() -> None:
    line = map_verified_identity(
        _assertion("same-opaque-id", source_system=SourceSystem.LINE)
    )
    partner = map_verified_identity(
        _assertion("same-opaque-id", source_system=SourceSystem.PARTNER)
    )

    assert line.effective_user_id != partner.effective_user_id
    assert line.external_user_id_hash != partner.external_user_id_hash


def test_two_synthetic_students_never_share_effective_id() -> None:
    student_a = map_verified_identity(_assertion("synthetic-student-a"))
    student_b = map_verified_identity(_assertion("synthetic-student-b"))

    assert student_a.effective_user_id != student_b.effective_user_id


def test_unverified_identity_fails_closed() -> None:
    with pytest.raises(IdentityMappingError, match="unverified"):
        map_verified_identity(_assertion(verified=False))


def test_synthetic_source_requires_an_explicit_synthetic_identifier() -> None:
    with pytest.raises(IdentityMappingError, match="synthetic prefix"):
        _assertion("student-without-prefix")


def test_other_tenant_fails_closed() -> None:
    with pytest.raises(IdentityMappingError, match="only the Xie Wenxian"):
        map_verified_identity(_assertion(), tenant_id="other_persona")


@pytest.mark.parametrize("external_id", ["", "has whitespace", "/path", "a" * 129])
def test_unbounded_or_unsafe_external_id_is_rejected(external_id: str) -> None:
    with pytest.raises(IdentityMappingError, match="bounded opaque"):
        _assertion(external_id)
