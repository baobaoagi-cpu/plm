from __future__ import annotations

import pytest

from duplex_voice.tts.generation_state import (
    ALLOWED_GENERATION_TRANSITIONS,
    TERMINAL_GENERATION_STATES,
    GenerationState,
    GenerationStateChanged,
)


def test_generation_state_values_are_stable() -> None:
    assert {state.value for state in GenerationState} == {
        "created",
        "active",
        "cancelling",
        "cancelled",
        "completed",
        "failed",
        "superseded",
    }


def test_transition_table_matches_approved_lifecycle() -> None:
    assert ALLOWED_GENERATION_TRANSITIONS[GenerationState.CREATED] == {
        GenerationState.ACTIVE,
        GenerationState.CANCELLED,
        GenerationState.FAILED,
    }
    assert ALLOWED_GENERATION_TRANSITIONS[GenerationState.ACTIVE] == {
        GenerationState.CANCELLING,
        GenerationState.COMPLETED,
        GenerationState.FAILED,
        GenerationState.SUPERSEDED,
    }
    assert ALLOWED_GENERATION_TRANSITIONS[GenerationState.CANCELLING] == {
        GenerationState.CANCELLED,
        GenerationState.FAILED,
    }


@pytest.mark.parametrize("state", TERMINAL_GENERATION_STATES)
def test_terminal_states_have_no_outgoing_transition(state: GenerationState) -> None:
    assert not ALLOWED_GENERATION_TRANSITIONS[state]


def test_structured_event_serializes_enums_and_monotonic_time() -> None:
    event = GenerationStateChanged(
        event="generation_state_changed",
        session_id="session-safe-hash",
        generation_id="00000000-0000-4000-8000-000000000000",
        from_state=GenerationState.ACTIVE,
        to_state=GenerationState.COMPLETED,
        reason=None,
        timestamp_monotonic_ms=123,
    )

    assert event.to_dict() == {
        "event": "generation_state_changed",
        "session_id": "session-safe-hash",
        "generation_id": "00000000-0000-4000-8000-000000000000",
        "from_state": "active",
        "to_state": "completed",
        "reason": None,
        "timestamp_monotonic_ms": 123,
    }
