"""Provider-independent generation lifecycle models and safe errors."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class GenerationState(StrEnum):
    CREATED = "created"
    ACTIVE = "active"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"
    SUPERSEDED = "superseded"


TERMINAL_GENERATION_STATES = frozenset(
    {
        GenerationState.CANCELLED,
        GenerationState.COMPLETED,
        GenerationState.FAILED,
        GenerationState.SUPERSEDED,
    }
)

ALLOWED_GENERATION_TRANSITIONS: dict[GenerationState, frozenset[GenerationState]] = {
    GenerationState.CREATED: frozenset(
        {GenerationState.ACTIVE, GenerationState.CANCELLED, GenerationState.FAILED}
    ),
    GenerationState.ACTIVE: frozenset(
        {
            GenerationState.CANCELLING,
            GenerationState.COMPLETED,
            GenerationState.FAILED,
            GenerationState.SUPERSEDED,
        }
    ),
    GenerationState.CANCELLING: frozenset(
        {GenerationState.CANCELLED, GenerationState.FAILED}
    ),
    GenerationState.CANCELLED: frozenset(),
    GenerationState.COMPLETED: frozenset(),
    GenerationState.FAILED: frozenset(),
    GenerationState.SUPERSEDED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class GenerationToken:
    session_id: str
    generation_id: str
    sequence: int


@dataclass(slots=True)
class GenerationRecord:
    token: GenerationToken
    state: GenerationState
    created_at_monotonic: float
    activated_at_monotonic: float | None = None
    finished_at_monotonic: float | None = None
    cancel_reason: str | None = None
    failure_reason: str | None = None
    metadata: dict[str, object] = field(default_factory=dict, repr=False)


@dataclass(frozen=True, slots=True)
class GenerationStateChanged:
    event: str
    session_id: str
    generation_id: str
    from_state: GenerationState | None
    to_state: GenerationState
    reason: str | None
    timestamp_monotonic_ms: int

    def to_dict(self) -> dict[str, str | int | None]:
        return {
            "event": self.event,
            "session_id": self.session_id,
            "generation_id": self.generation_id,
            "from_state": self.from_state.value if self.from_state is not None else None,
            "to_state": self.to_state.value,
            "reason": self.reason,
            "timestamp_monotonic_ms": self.timestamp_monotonic_ms,
        }


class GenerationGuardError(RuntimeError):
    """Base class for errors whose messages never contain metadata."""


class UnknownGenerationError(GenerationGuardError):
    """Raised when a token does not identify a known generation."""


class GenerationSessionMismatchError(GenerationGuardError):
    """Raised when a known generation is presented with the wrong session."""


class InvalidGenerationTransitionError(GenerationGuardError):
    """Raised for a lifecycle transition outside the mechanical transition table."""


class GenerationNotAcceptingError(GenerationGuardError):
    """Raised when data targets a generation that is not the active generation."""


class ActiveGenerationConflictError(GenerationGuardError):
    """Raised when activation would create two active generations in one session."""


class GenerationMetadataError(GenerationGuardError):
    """Raised when metadata cannot be retained safely."""
