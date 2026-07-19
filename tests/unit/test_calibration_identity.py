import pytest

from duplex_voice.calibration.identity import (
    SANDBOX_NOTICE,
    XIEWENXIAN_NAMESPACES,
    XIEWENXIAN_SECRET_SLOTS,
    CalibrationAccessDenied,
    CalibrationPermission,
    CalibrationRole,
    NamespaceBinding,
    OwnerCalibrationPolicy,
    load_owner_calibration_policy,
    parse_line_allowlist,
)


def _enabled_policy() -> OwnerCalibrationPolicy:
    return OwnerCalibrationPolicy(
        roles_by_line_user_id={
            "U-owner": CalibrationRole.OWNER,
            "U-governor": CalibrationRole.GOVERNOR,
            "U-tester": CalibrationRole.TECHNICAL_TESTER,
        },
        enabled=True,
        kill_switch=False,
    )


def test_xiewenxian_binding_is_disjoint_from_other_persona_tenant() -> None:
    existing = NamespaceBinding(
        tenant_id="other_persona",
        persona_id="other_persona_v1",
        persona_version_binding="other-persona-v1.0",
        memory_namespace="other_persona/production",
        mem0_user_id="other_persona/owner",
        database_tenant="other_persona",
        audio_prefix="other_persona/audio",
        transcript_prefix="other_persona/transcripts",
        livekit_room_namespace="other_persona/livekit",
        prompt_cache_namespace="other_persona/prompt-cache",
        session_state_namespace="other_persona/session-state",
    )

    XIEWENXIAN_NAMESPACES.assert_disjoint_from(existing)


def test_namespace_overlap_fails_closed() -> None:
    duplicate = NamespaceBinding(
        tenant_id="other",
        persona_id="other_calibration",
        persona_version_binding="other-v0.1",
        memory_namespace=XIEWENXIAN_NAMESPACES.memory_namespace,
        mem0_user_id="other/owner",
        database_tenant="other",
        audio_prefix="other/audio",
        transcript_prefix="other/transcripts",
        livekit_room_namespace="other/livekit",
        prompt_cache_namespace="other/prompt-cache",
        session_state_namespace="other/session-state",
    )

    with pytest.raises(ValueError, match="命名空間不得共用"):
        XIEWENXIAN_NAMESPACES.assert_disjoint_from(duplicate)


def test_secret_slots_are_unique_and_persona_scoped() -> None:
    XIEWENXIAN_SECRET_SLOTS.validate()
    assert len(set(XIEWENXIAN_SECRET_SLOTS.values())) == 8
    assert all(
        slot.startswith("XIEWENXIAN_CALIBRATION_")
        for slot in XIEWENXIAN_SECRET_SLOTS.values()
    )


def test_unknown_line_user_is_denied() -> None:
    decision = _enabled_policy().authorize("U-unknown")

    assert decision.allowed is False
    assert decision.role is CalibrationRole.DENIED
    assert decision.reason == "line_user_not_allowlisted"


def test_owner_and_governor_permissions_are_distinct() -> None:
    policy = _enabled_policy()

    owner_evidence = policy.authorize(
        "U-owner", CalibrationPermission.SUBMIT_OWNER_EVIDENCE
    )
    governor_evidence = policy.authorize(
        "U-governor", CalibrationPermission.SUBMIT_OWNER_EVIDENCE
    )
    governor_review = policy.authorize("U-governor", CalibrationPermission.GOVERN)

    assert owner_evidence.allowed is True
    assert owner_evidence.may_create_owner_evidence is True
    assert governor_evidence.allowed is False
    assert governor_evidence.may_create_owner_evidence is False
    assert governor_review.allowed is True


@pytest.mark.parametrize(
    ("enabled", "kill_switch", "reason"),
    [
        (False, False, "sandbox_disabled"),
        (True, True, "kill_switch_active"),
    ],
)
def test_disabled_or_killed_sandbox_stops_all_responses(
    enabled: bool, kill_switch: bool, reason: str
) -> None:
    policy = OwnerCalibrationPolicy(
        roles_by_line_user_id={"U-owner": CalibrationRole.OWNER},
        enabled=enabled,
        kill_switch=kill_switch,
    )

    with pytest.raises(CalibrationAccessDenied, match=reason):
        policy.require_response_allowed("U-owner")


def test_sandbox_response_always_has_calibration_notice() -> None:
    rendered = _enabled_policy().decorate_sandbox_response("測試回答")

    assert rendered.startswith("【本人校準版】")
    assert SANDBOX_NOTICE in rendered
    assert rendered.endswith("測試回答")


def test_policy_defaults_fail_closed_without_environment() -> None:
    policy = load_owner_calibration_policy({})

    assert policy.enabled is False
    assert policy.kill_switch is True
    assert policy.sandbox_mode is True
    assert policy.roles_by_line_user_id == {}


def test_allowlist_is_loaded_from_json_without_repository_identity_data() -> None:
    roles = parse_line_allowlist(
        '{"U-owner":"OWNER","U-governor":"GOVERNOR",'
        '"U-tester":"TECHNICAL_TESTER"}'
    )

    assert roles == {
        "U-owner": CalibrationRole.OWNER,
        "U-governor": CalibrationRole.GOVERNOR,
        "U-tester": CalibrationRole.TECHNICAL_TESTER,
    }


def test_non_sandbox_configuration_is_rejected() -> None:
    with pytest.raises(ValueError, match="不得關閉 sandbox mode"):
        OwnerCalibrationPolicy(
            roles_by_line_user_id={},
            sandbox_mode=False,
        )
