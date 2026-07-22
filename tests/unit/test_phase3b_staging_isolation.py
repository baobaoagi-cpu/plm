from __future__ import annotations

import pytest

from duplex_voice.calibration.identity_mapping import (
    PrincipalIdentity,
    PrincipalKind,
    SourceSystem,
    VerifiedIdentityAssertion,
    map_verified_identity,
)
from duplex_voice.calibration.staging_store import (
    IsolationViolation,
    MemoryOrigin,
    StagingIsolationStore,
)


def _principal(external_id: str, kind: PrincipalKind) -> PrincipalIdentity:
    return map_verified_identity(
        VerifiedIdentityAssertion(
            source_system=SourceSystem.SYNTHETIC,
            external_user_id=external_id,
            principal_kind=kind,
            verified=True,
        )
    )


def test_synthetic_conversations_are_isolated_both_directions() -> None:
    store = StagingIsolationStore()
    student_a = _principal("synthetic-student-a", PrincipalKind.STUDENT)
    student_b = _principal("synthetic-student-b", PrincipalKind.STUDENT)
    record_a = store.add_conversation(student_a, "synthetic:A-only conversation")
    record_b = store.add_conversation(student_b, "synthetic:B-only conversation")

    assert store.list_conversations(student_a) == (record_a,)
    assert store.list_conversations(student_b) == (record_b,)
    with pytest.raises(IsolationViolation, match="principal boundary"):
        store.get_conversation(student_a, record_b.record_id)
    with pytest.raises(IsolationViolation, match="principal boundary"):
        store.get_conversation(student_b, record_a.record_id)


def test_synthetic_content_is_stored_only_as_digest() -> None:
    store = StagingIsolationStore()
    student = _principal("synthetic-student", PrincipalKind.STUDENT)
    content = "synthetic:private content"

    record = store.add_conversation(student, content)

    assert record.content_digest != content
    assert len(record.content_digest) == 64


def test_student_memory_isolated_between_students() -> None:
    store = StagingIsolationStore()
    student_a = _principal("synthetic-student-a", PrincipalKind.STUDENT)
    student_b = _principal("synthetic-student-b", PrincipalKind.STUDENT)
    memory_a = store.add_student_memory(student_a, "synthetic:A-memory")
    memory_b = store.add_student_memory(student_b, "synthetic:B-memory")

    assert store.list_student_memories(student_a) == (memory_a,)
    assert store.list_student_memories(student_b) == (memory_b,)
    assert memory_a.origin is MemoryOrigin.STUDENT_CONVERSATION


def test_prompt_logs_are_isolated_between_students() -> None:
    store = StagingIsolationStore()
    student_a = _principal("synthetic-student-a", PrincipalKind.STUDENT)
    student_b = _principal("synthetic-student-b", PrincipalKind.STUDENT)
    prompt_a = store.add_prompt_log(student_a, "synthetic:A-prompt")
    prompt_b = store.add_prompt_log(student_b, "synthetic:B-prompt")

    assert store.list_prompt_logs(student_a) == (prompt_a,)
    assert store.list_prompt_logs(student_b) == (prompt_b,)


def test_only_owner_can_submit_owner_evidence() -> None:
    store = StagingIsolationStore()
    owner = _principal("synthetic-owner", PrincipalKind.OWNER)
    student = _principal("synthetic-student", PrincipalKind.STUDENT)
    evidence = store.add_owner_evidence(
        owner,
        candidate_id="xww-v2-persona-001",
        synthetic_evidence="synthetic:owner correction",
    )

    assert store.list_owner_evidence(owner) == (evidence,)
    assert evidence.review_state == "OWNER_PROVIDED_UNREVIEWED"
    with pytest.raises(IsolationViolation, match="only the verified owner"):
        store.add_owner_evidence(
            student,
            candidate_id="xww-v2-persona-001",
            synthetic_evidence="synthetic:not owner evidence",
        )


def test_owner_evidence_cannot_enter_student_memory() -> None:
    store = StagingIsolationStore()
    owner = _principal("synthetic-owner", PrincipalKind.OWNER)
    student = _principal("synthetic-student", PrincipalKind.STUDENT)

    with pytest.raises(IsolationViolation, match="only student principals"):
        store.add_student_memory(owner, "synthetic:owner evidence")
    with pytest.raises(IsolationViolation, match="cannot enter student memory"):
        store.add_student_memory(
            student,
            "synthetic:owner evidence",
            origin=MemoryOrigin.OWNER_EVIDENCE,
        )


def test_wrong_tenant_is_rejected_even_with_valid_effective_id() -> None:
    store = StagingIsolationStore()
    valid = _principal("synthetic-student", PrincipalKind.STUDENT)
    wrong_tenant = PrincipalIdentity(
        tenant_id="other_persona",
        source_system=valid.source_system,
        principal_kind=valid.principal_kind,
        effective_user_id=valid.effective_user_id,
        external_user_id_hash=valid.external_user_id_hash,
    )

    with pytest.raises(IsolationViolation, match="tenant boundary"):
        store.add_conversation(wrong_tenant, "synthetic:must fail")


def test_safe_counts_contain_no_identity_or_content() -> None:
    store = StagingIsolationStore()
    student = _principal("synthetic-student", PrincipalKind.STUDENT)
    store.add_conversation(student, "synthetic:conversation")
    store.add_student_memory(student, "synthetic:memory")
    store.add_prompt_log(student, "synthetic:prompt")

    assert store.safe_counts() == {
        "conversations": 1,
        "student_memories": 1,
        "prompt_logs": 1,
        "owner_evidence": 0,
    }


def test_store_rejects_content_not_explicitly_marked_synthetic() -> None:
    store = StagingIsolationStore()
    student = _principal("synthetic-student", PrincipalKind.STUDENT)

    with pytest.raises(ValueError, match="only bounded synthetic"):
        store.add_conversation(student, "unlabelled content")
