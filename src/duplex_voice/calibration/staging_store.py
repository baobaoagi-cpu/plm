"""In-memory Phase 3B store used only to prove isolation contracts.

This is not a production repository and deliberately has no database or Mem0 adapter.  It mirrors
the invariants enforced by the PostgreSQL staging migration so they can be tested without external
infrastructure or real user data.
"""

from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass
from enum import StrEnum

from duplex_voice.calibration.identity import XIEWENXIAN_NAMESPACES
from duplex_voice.calibration.identity_mapping import PrincipalIdentity, PrincipalKind


class IsolationViolation(PermissionError):
    """Raised when data crosses a tenant, principal, or evidence boundary."""


class MemoryOrigin(StrEnum):
    STUDENT_CONVERSATION = "student_conversation"
    OWNER_EVIDENCE = "owner_evidence"


@dataclass(frozen=True, slots=True)
class ConversationRecord:
    record_id: int
    tenant_id: str
    effective_user_id: str
    content_digest: str


@dataclass(frozen=True, slots=True)
class StudentMemoryRecord:
    record_id: int
    tenant_id: str
    effective_user_id: str
    memory_digest: str
    origin: MemoryOrigin


@dataclass(frozen=True, slots=True)
class PromptLogRecord:
    record_id: int
    tenant_id: str
    effective_user_id: str
    prompt_digest: str


@dataclass(frozen=True, slots=True)
class OwnerEvidenceRecord:
    record_id: int
    tenant_id: str
    effective_user_id: str
    candidate_id: str
    evidence_digest: str
    review_state: str = "OWNER_PROVIDED_UNREVIEWED"


class StagingIsolationStore:
    """Thread-safe proof store with mandatory principal scope on every operation."""

    def __init__(self, *, tenant_id: str = XIEWENXIAN_NAMESPACES.tenant_id) -> None:
        if tenant_id != XIEWENXIAN_NAMESPACES.tenant_id:
            raise IsolationViolation("only the Xie Wenxian staging tenant is allowed")
        self._tenant_id = tenant_id
        self._lock = threading.RLock()
        self._next_id = 1
        self._conversations: dict[int, ConversationRecord] = {}
        self._student_memories: dict[int, StudentMemoryRecord] = {}
        self._prompt_logs: dict[int, PromptLogRecord] = {}
        self._owner_evidence: dict[int, OwnerEvidenceRecord] = {}

    def add_conversation(
        self, principal: PrincipalIdentity, synthetic_content: str
    ) -> ConversationRecord:
        self._require_scope(principal)
        with self._lock:
            record = ConversationRecord(
                self._allocate_id_locked(),
                self._tenant_id,
                principal.effective_user_id,
                self._digest(synthetic_content),
            )
            self._conversations[record.record_id] = record
            return record

    def get_conversation(
        self, principal: PrincipalIdentity, record_id: int
    ) -> ConversationRecord:
        self._require_scope(principal)
        with self._lock:
            record = self._conversations[record_id]
            self._require_owner(principal, record.tenant_id, record.effective_user_id)
            return record

    def list_conversations(
        self, principal: PrincipalIdentity
    ) -> tuple[ConversationRecord, ...]:
        self._require_scope(principal)
        with self._lock:
            return tuple(
                record
                for record in self._conversations.values()
                if record.tenant_id == principal.tenant_id
                and record.effective_user_id == principal.effective_user_id
            )

    def add_student_memory(
        self,
        principal: PrincipalIdentity,
        synthetic_memory: str,
        *,
        origin: MemoryOrigin = MemoryOrigin.STUDENT_CONVERSATION,
    ) -> StudentMemoryRecord:
        self._require_scope(principal)
        if principal.principal_kind is not PrincipalKind.STUDENT:
            raise IsolationViolation("student memory accepts only student principals")
        if origin is not MemoryOrigin.STUDENT_CONVERSATION:
            raise IsolationViolation("owner evidence cannot enter student memory")
        with self._lock:
            record = StudentMemoryRecord(
                self._allocate_id_locked(),
                self._tenant_id,
                principal.effective_user_id,
                self._digest(synthetic_memory),
                origin,
            )
            self._student_memories[record.record_id] = record
            return record

    def list_student_memories(
        self, principal: PrincipalIdentity
    ) -> tuple[StudentMemoryRecord, ...]:
        self._require_scope(principal)
        if principal.principal_kind is not PrincipalKind.STUDENT:
            raise IsolationViolation("student memory accepts only student principals")
        with self._lock:
            return tuple(
                record
                for record in self._student_memories.values()
                if record.tenant_id == principal.tenant_id
                and record.effective_user_id == principal.effective_user_id
            )

    def add_prompt_log(
        self, principal: PrincipalIdentity, synthetic_prompt: str
    ) -> PromptLogRecord:
        self._require_scope(principal)
        with self._lock:
            record = PromptLogRecord(
                self._allocate_id_locked(),
                self._tenant_id,
                principal.effective_user_id,
                self._digest(synthetic_prompt),
            )
            self._prompt_logs[record.record_id] = record
            return record

    def list_prompt_logs(self, principal: PrincipalIdentity) -> tuple[PromptLogRecord, ...]:
        self._require_scope(principal)
        with self._lock:
            return tuple(
                record
                for record in self._prompt_logs.values()
                if record.tenant_id == principal.tenant_id
                and record.effective_user_id == principal.effective_user_id
            )

    def add_owner_evidence(
        self,
        principal: PrincipalIdentity,
        *,
        candidate_id: str,
        synthetic_evidence: str,
    ) -> OwnerEvidenceRecord:
        self._require_scope(principal)
        if principal.principal_kind is not PrincipalKind.OWNER:
            raise IsolationViolation("owner evidence accepts only the verified owner")
        if not candidate_id.startswith("xww-v2-"):
            raise ValueError("candidate ID must be a governed Xie Wenxian candidate")
        with self._lock:
            record = OwnerEvidenceRecord(
                self._allocate_id_locked(),
                self._tenant_id,
                principal.effective_user_id,
                candidate_id,
                self._digest(synthetic_evidence),
            )
            self._owner_evidence[record.record_id] = record
            return record

    def list_owner_evidence(
        self, principal: PrincipalIdentity
    ) -> tuple[OwnerEvidenceRecord, ...]:
        self._require_scope(principal)
        if principal.principal_kind is not PrincipalKind.OWNER:
            raise IsolationViolation("owner evidence accepts only the verified owner")
        with self._lock:
            return tuple(
                record
                for record in self._owner_evidence.values()
                if record.tenant_id == principal.tenant_id
                and record.effective_user_id == principal.effective_user_id
            )

    def safe_counts(self) -> dict[str, int]:
        with self._lock:
            return {
                "conversations": len(self._conversations),
                "student_memories": len(self._student_memories),
                "prompt_logs": len(self._prompt_logs),
                "owner_evidence": len(self._owner_evidence),
            }

    def _require_scope(self, principal: PrincipalIdentity) -> None:
        if principal.tenant_id != self._tenant_id:
            raise IsolationViolation("tenant boundary violation")

    @staticmethod
    def _require_owner(
        principal: PrincipalIdentity, tenant_id: str, effective_user_id: str
    ) -> None:
        if (
            tenant_id != principal.tenant_id
            or effective_user_id != principal.effective_user_id
        ):
            raise IsolationViolation("principal boundary violation")

    def _allocate_id_locked(self) -> int:
        record_id = self._next_id
        self._next_id += 1
        return record_id

    @staticmethod
    def _digest(value: str) -> str:
        if not value.startswith("synthetic:") or len(value) > 1_000:
            raise ValueError("Phase 3B accepts only bounded synthetic proof content")
        return hashlib.sha256(value.encode()).hexdigest()


__all__ = [
    "ConversationRecord",
    "IsolationViolation",
    "MemoryOrigin",
    "OwnerEvidenceRecord",
    "PromptLogRecord",
    "StagingIsolationStore",
    "StudentMemoryRecord",
]
