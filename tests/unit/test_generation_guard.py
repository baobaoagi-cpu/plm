from __future__ import annotations

import ast
import asyncio
import json
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from duplex_voice.tts.generation_guard import GenerationGuard
from duplex_voice.tts.generation_state import (
    ActiveGenerationConflictError,
    GenerationMetadataError,
    GenerationNotAcceptingError,
    GenerationSessionMismatchError,
    GenerationState,
    GenerationStateChanged,
    GenerationToken,
    InvalidGenerationTransitionError,
    UnknownGenerationError,
)


class FakeClock:
    def __init__(self, value: float = 100.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def active_token(guard: GenerationGuard, session_id: str = "session-a") -> GenerationToken:
    token = guard.create(session_id)
    guard.activate(token)
    return token


def test_create_generates_unique_collision_safe_ids_and_monotonic_sequences() -> None:
    guard = GenerationGuard()
    tokens = [guard.create("session-a") for _ in range(100)]

    assert len({token.generation_id for token in tokens}) == 100
    assert [token.sequence for token in tokens] == list(range(1, 101))


def test_sequences_are_independent_per_session() -> None:
    guard = GenerationGuard()

    assert guard.create("session-a").sequence == 1
    assert guard.create("session-b").sequence == 1
    assert guard.create("session-a").sequence == 2


def test_created_to_active_to_completed() -> None:
    guard = GenerationGuard()
    token = guard.create("session-a")

    guard.activate(token)
    assert guard.get_state(token) is GenerationState.ACTIVE
    assert guard.complete(token)
    assert guard.get_state(token) is GenerationState.COMPLETED
    assert guard.is_terminal(token)
    assert guard.get_active("session-a") is None


def test_active_to_cancelling_to_cancelled() -> None:
    guard = GenerationGuard()
    token = active_token(guard)

    assert guard.begin_cancel(token, "user_interruption")
    assert guard.get_state(token) is GenerationState.CANCELLING
    assert not guard.should_accept(token)
    assert guard.mark_cancelled(token)
    assert guard.get_state(token) is GenerationState.CANCELLED


def test_created_can_be_cancelled_without_activation() -> None:
    guard = GenerationGuard()
    token = guard.create("session-a")

    assert guard.cancel(token, "call_ended")
    assert guard.get_state(token) is GenerationState.CANCELLED


def test_active_can_fail() -> None:
    guard = GenerationGuard()
    token = active_token(guard)

    assert guard.fail(token, "provider_error")
    assert guard.get_state(token) is GenerationState.FAILED
    assert guard.get_record(token).failure_reason == "provider_error"


def test_active_can_be_superseded() -> None:
    guard = GenerationGuard()
    token = active_token(guard)

    assert guard.supersede(token, "newer_generation")
    assert guard.get_state(token) is GenerationState.SUPERSEDED
    assert guard.get_record(token).cancel_reason == "newer_generation"


@pytest.mark.parametrize(
    ("finish", "expected"),
    [
        (lambda guard, token: guard.cancel(token, "call_ended"), GenerationState.CANCELLED),
        (lambda guard, token: guard.complete(token), GenerationState.COMPLETED),
        (lambda guard, token: guard.fail(token, "provider_error"), GenerationState.FAILED),
        (
            lambda guard, token: guard.supersede(token, "newer_generation"),
            GenerationState.SUPERSEDED,
        ),
    ],
)
def test_terminal_generation_cannot_be_reactivated(
    finish: Callable[[GenerationGuard, GenerationToken], bool], expected: GenerationState
) -> None:
    guard = GenerationGuard()
    token = active_token(guard)
    assert finish(guard, token)

    with pytest.raises(InvalidGenerationTransitionError):
        guard.activate(token)
    assert guard.get_state(token) is expected


@pytest.mark.parametrize(
    "terminal_action",
    [
        lambda guard, token: guard.cancel(token, "user_interruption"),
        lambda guard, token: guard.complete(token),
        lambda guard, token: guard.fail(token, "provider_error"),
    ],
)
@pytest.mark.parametrize(
    "late_data_kind",
    [
        "llm_text_delta",
        "semantic_text_chunk",
        "minimax_protocol_event",
        "audio_chunk",
        "playback_queue_item",
        "task_finished_event",
        "provider_error",
    ],
)
def test_terminal_generation_rejects_every_late_data_kind(
    terminal_action: Callable[[GenerationGuard, GenerationToken], bool], late_data_kind: str
) -> None:
    guard = GenerationGuard()
    token = active_token(guard)
    assert terminal_action(guard, token)

    assert late_data_kind
    assert not guard.should_accept(token)
    with pytest.raises(GenerationNotAcceptingError):
        guard.assert_accepting(token)


def test_replace_active_supersedes_old_before_activating_new() -> None:
    events: list[GenerationStateChanged] = []
    guard = GenerationGuard(event_sink=events.append)
    old = active_token(guard)

    new = guard.replace_active("session-a", "newer_generation")

    assert guard.get_state(old) is GenerationState.SUPERSEDED
    assert guard.get_state(new) is GenerationState.ACTIVE
    assert guard.get_active("session-a") == new
    superseded_index = next(
        index
        for index, event in enumerate(events)
        if event.generation_id == old.generation_id
        and event.to_state is GenerationState.SUPERSEDED
    )
    new_active_index = next(
        index
        for index, event in enumerate(events)
        if event.generation_id == new.generation_id and event.to_state is GenerationState.ACTIVE
    )
    assert superseded_index < new_active_index


def test_activate_refuses_second_active_in_same_session() -> None:
    guard = GenerationGuard()
    active_token(guard)
    second = guard.create("session-a")

    with pytest.raises(ActiveGenerationConflictError):
        guard.activate(second)
    assert guard.get_state(second) is GenerationState.CREATED


def test_different_sessions_can_each_have_an_active_generation() -> None:
    guard = GenerationGuard()
    first = active_token(guard, "session-a")
    second = active_token(guard, "session-b")

    assert guard.get_active("session-a") == first
    assert guard.get_active("session-b") == second
    assert guard.should_accept(first)
    assert guard.should_accept(second)


def test_session_mismatch_and_unknown_tokens_are_rejected() -> None:
    guard = GenerationGuard()
    token = active_token(guard)
    mismatch = GenerationToken("session-b", token.generation_id, token.sequence)
    unknown = GenerationToken("session-a", "00000000-0000-4000-8000-000000000000", 999)

    assert not guard.should_accept(mismatch)
    assert not guard.should_accept(unknown)
    with pytest.raises(GenerationSessionMismatchError):
        guard.get_state(mismatch)
    with pytest.raises(UnknownGenerationError):
        guard.get_state(unknown)


def test_duplicate_cancel_is_safe_and_idempotent() -> None:
    guard = GenerationGuard()
    token = active_token(guard)

    assert guard.cancel(token, "user_interruption")
    assert not guard.cancel(token, "user_interruption")
    assert guard.get_state(token) is GenerationState.CANCELLED


@pytest.mark.asyncio
async def test_cancel_and_complete_race_is_atomic() -> None:
    guard = GenerationGuard()
    token = active_token(guard)
    barrier = threading.Barrier(2)

    def cancel() -> bool:
        barrier.wait()
        return guard.cancel(token, "user_interruption")

    def complete() -> bool:
        barrier.wait()
        return guard.complete(token)

    results = await asyncio.gather(asyncio.to_thread(cancel), asyncio.to_thread(complete))

    assert sum(results) == 1
    assert guard.get_state(token) in {GenerationState.CANCELLED, GenerationState.COMPLETED}
    assert guard.is_terminal(token)


def test_one_hundred_late_audio_chunks_drop_without_exception_storm() -> None:
    guard = GenerationGuard()
    token = active_token(guard)
    guard.cancel(token, "user_interruption")

    accepted = [guard.should_accept(token) for _ in range(100)]

    assert accepted == [False] * 100


def test_cleanup_never_deletes_live_states_and_deletes_old_terminal() -> None:
    clock = FakeClock()
    guard = GenerationGuard(monotonic=clock, terminal_ttl_s=10.0)
    active = active_token(guard, "session-active")
    created = guard.create("session-created")
    cancelling = active_token(guard, "session-cancelling")
    guard.begin_cancel(cancelling, "user_interruption")
    terminal = active_token(guard, "session-terminal")
    guard.complete(terminal)
    clock.advance(11.0)

    assert guard.cleanup() == 1
    assert guard.get_state(active) is GenerationState.ACTIVE
    assert guard.get_state(created) is GenerationState.CREATED
    assert guard.get_state(cancelling) is GenerationState.CANCELLING
    with pytest.raises(UnknownGenerationError):
        guard.get_state(terminal)


def test_cleanup_enforces_terminal_capacity() -> None:
    clock = FakeClock()
    guard = GenerationGuard(monotonic=clock, terminal_ttl_s=1_000.0, max_terminal_records=2)
    tokens: list[GenerationToken] = []
    for index in range(3):
        token = active_token(guard, f"session-{index}")
        guard.complete(token)
        tokens.append(token)
        clock.advance(1.0)

    assert guard.cleanup(cutoff_monotonic=0.0) == 1
    with pytest.raises(UnknownGenerationError):
        guard.get_state(tokens[0])
    assert guard.is_terminal(tokens[1])
    assert guard.is_terminal(tokens[2])


def test_snapshot_and_events_do_not_leak_metadata_or_raw_session_id() -> None:
    events: list[GenerationStateChanged] = []
    guard = GenerationGuard(event_sink=events.append)
    token = guard.create(
        "opaque-session-123", {"request_class": "interactive", "attempt": 1}
    )
    guard.activate(token)

    rendered = json.dumps(guard.snapshot())
    event_rendered = json.dumps([event.to_dict() for event in events])
    assert "request_class" not in rendered
    assert "interactive" not in rendered
    assert "opaque-session-123" not in rendered
    assert "opaque-session-123" not in event_rendered
    assert token.generation_id in rendered
    assert token.generation_id in event_rendered


@pytest.mark.parametrize(
    "metadata",
    [
        {"api_key": "not-a-real-key"},
        {"voice_id": "not-a-real-voice"},
        {"authorization": "not-a-real-header"},
        {"prompt": "private words"},
        {"nested": {"unsafe": True}},
        {"too_long": "x" * 257},
    ],
)
def test_sensitive_or_non_scalar_metadata_is_rejected(metadata: dict[str, object]) -> None:
    guard = GenerationGuard()

    with pytest.raises(GenerationMetadataError, match="metadata"):
        guard.create("session-a", metadata)


def test_get_record_returns_a_detached_metadata_copy() -> None:
    guard = GenerationGuard()
    token = guard.create("session-a", {"attempt": 1})

    detached = guard.get_record(token)
    detached.metadata["attempt"] = 999

    assert guard.get_record(token).metadata == {"attempt": 1}


def test_cancel_active_is_session_scoped() -> None:
    guard = GenerationGuard()
    first = active_token(guard, "session-a")
    second = active_token(guard, "session-b")

    assert guard.cancel_active("session-a", "call_ended") == first
    assert guard.get_state(first) is GenerationState.CANCELLED
    assert guard.get_state(second) is GenerationState.ACTIVE
    assert guard.cancel_active("session-a", "call_ended") is None


@pytest.mark.asyncio
async def test_concurrent_replace_active_leaves_exactly_one_active() -> None:
    guard = GenerationGuard()
    active_token(guard)
    worker_count = 20
    barrier = threading.Barrier(worker_count)

    def replace() -> GenerationToken:
        barrier.wait()
        return guard.replace_active("session-a", "newer_generation")

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        tokens = await asyncio.gather(
            *(loop.run_in_executor(executor, replace) for _ in range(worker_count))
        )

    current = guard.get_active("session-a")
    assert current in tokens
    assert len({token.generation_id for token in tokens}) == worker_count
    assert sum(guard.get_state(token) is GenerationState.ACTIVE for token in tokens) == 1
    assert sum(guard.get_state(token) is GenerationState.SUPERSEDED for token in tokens) == 19
    assert guard.snapshot()["active_count"] == 1


def test_event_sink_runs_outside_lock() -> None:
    callback_completed = threading.Event()
    guard: GenerationGuard

    def read_snapshot() -> None:
        guard.snapshot()
        callback_completed.set()

    def sink(_: GenerationStateChanged) -> None:
        worker = threading.Thread(target=read_snapshot)
        worker.start()
        worker.join(timeout=1.0)
        assert callback_completed.is_set()

    guard = GenerationGuard(event_sink=sink)
    guard.create("session-a")


def test_generation_guard_has_no_forbidden_runtime_imports() -> None:
    source_paths = [
        Path("src/duplex_voice/tts/generation_guard.py"),
        Path("src/duplex_voice/tts/generation_state.py"),
    ]
    imported_roots: set[str] = set()
    for path in source_paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint(
        {"pipecat", "livekit", "websockets", "line", "minimax_protocol"}
    )
