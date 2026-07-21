from __future__ import annotations

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from duplex_voice.audio.duplex_simulator import OfflineDuplexHarness
from duplex_voice.audio.formats import PCM16_MONO_16KHZ
from duplex_voice.audio.queue import AudioBackpressureError
from duplex_voice.tts.generation_state import GenerationState


def _pcm_frame() -> bytes:
    return bytes(PCM16_MONO_16KHZ.pcm_bytes_for_duration(20))


def test_pcm_frame_duration_is_exact_and_single_boundary_owned() -> None:
    frame = _pcm_frame()

    assert len(frame) == 640
    assert PCM16_MONO_16KHZ.pcm_duration_ms(len(frame)) == 20.0


def test_microphone_track_continues_while_assistant_track_is_buffered() -> None:
    harness = OfflineDuplexHarness("session-a")
    token = harness.start_generation()
    assert harness.receive_assistant_audio(
        token, sequence=1, payload=b"synthetic-mp3", duration_ms=40
    )

    for sequence in range(1, 11):
        harness.receive_microphone(
            sequence=sequence, payload=_pcm_frame(), duration_ms=20
        )

    assert harness.input_queue.stats().accepted_items == 10
    assert harness.input_queue.stats().pending_ms == 200
    assert harness.output_queue.stats().pending_ms == 40
    assert harness.play_next() is not None
    assert harness.input_queue.stats().queued_items == 10


def test_interruption_clears_local_audio_and_rejects_every_late_chunk() -> None:
    harness = OfflineDuplexHarness("session-a")
    token = harness.start_generation()
    for sequence in range(1, 6):
        assert harness.receive_assistant_audio(
            token, sequence=sequence, payload=b"synthetic-mp3", duration_ms=20
        )

    assert harness.interrupt(token) == 5
    assert harness.guard.get_state(token) is GenerationState.CANCELLED
    for sequence in range(6, 106):
        assert not harness.receive_assistant_audio(
            token, sequence=sequence, payload=b"late", duration_ms=20
        )

    assert harness.play_next() is None
    stats = harness.output_queue.stats()
    assert stats.cleared_items == 5
    assert stats.stale_items_dropped == 100
    assert stats.played_items == 0


def test_new_generation_plays_without_reviving_old_generation() -> None:
    harness = OfflineDuplexHarness("session-a")
    old = harness.start_generation()
    harness.receive_assistant_audio(old, sequence=1, payload=b"old", duration_ms=20)
    harness.interrupt(old)
    new = harness.start_generation()

    assert not harness.receive_assistant_audio(
        old, sequence=2, payload=b"late-old", duration_ms=20
    )
    assert harness.receive_assistant_audio(
        new, sequence=1, payload=b"new", duration_ms=20
    )
    played = harness.play_next()
    assert played is not None
    assert played.token == new
    assert played.payload == b"new"
    assert harness.play_next() is None


def test_input_and_output_backpressure_are_independent_and_bounded() -> None:
    harness = OfflineDuplexHarness(
        "session-a", input_max_pending_ms=20, output_max_pending_ms=20
    )
    token = harness.start_generation()
    harness.receive_microphone(sequence=1, payload=_pcm_frame(), duration_ms=20)
    harness.receive_assistant_audio(token, sequence=1, payload=b"mp3", duration_ms=20)

    with pytest.raises(AudioBackpressureError, match="input"):
        harness.receive_microphone(sequence=2, payload=_pcm_frame(), duration_ms=20)
    with pytest.raises(AudioBackpressureError, match="output"):
        harness.receive_assistant_audio(
            token, sequence=2, payload=b"mp3", duration_ms=20
        )

    assert harness.input_queue.stats().backpressure_rejections == 1
    assert harness.output_queue.stats().backpressure_rejections == 1


@pytest.mark.asyncio
async def test_interrupt_enqueue_race_never_returns_stale_audio_for_playback() -> None:
    harness = OfflineDuplexHarness("session-a", output_max_pending_ms=10_000)
    token = harness.start_generation()
    worker_count = 40
    barrier = threading.Barrier(worker_count + 1)

    def enqueue(sequence: int) -> bool:
        barrier.wait()
        return harness.receive_assistant_audio(
            token, sequence=sequence, payload=b"race", duration_ms=20
        )

    def interrupt() -> int:
        barrier.wait()
        return harness.interrupt(token)

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=worker_count + 1) as executor:
        results = await asyncio.gather(
            *(loop.run_in_executor(executor, enqueue, index) for index in range(1, 41)),
            loop.run_in_executor(executor, interrupt),
        )

    assert len(results) == 41
    assert harness.play_next() is None
    assert harness.output_queue.stats().played_items == 0
    assert harness.guard.get_state(token) is GenerationState.CANCELLED


def test_hangup_is_idempotent_and_clears_both_tracks() -> None:
    harness = OfflineDuplexHarness("session-a")
    token = harness.start_generation()
    harness.receive_microphone(sequence=1, payload=_pcm_frame(), duration_ms=20)
    harness.receive_assistant_audio(token, sequence=1, payload=b"mp3", duration_ms=20)

    harness.hangup()
    harness.hangup()

    assert harness.input_queue.stats().queued_items == 0
    assert harness.output_queue.stats().queued_items == 0
    assert harness.guard.get_active("session-a") is None


def test_one_hundred_interruptions_never_revive_old_audio() -> None:
    harness = OfflineDuplexHarness("session-a")

    for cycle in range(100):
        token = harness.start_generation()
        harness.receive_assistant_audio(token, sequence=1, payload=b"old", duration_ms=20)
        harness.interrupt(token)
        assert not harness.receive_assistant_audio(
            token, sequence=2, payload=b"late", duration_ms=20
        )
        assert harness.play_next() is None, cycle

    assert harness.output_queue.stats().played_items == 0
    assert harness.output_queue.stats().stale_items_dropped == 100
