from __future__ import annotations

import asyncio

import pytest
from tests.fakes.providers import (
    FakeGenerationTTS,
    FakeStreamingLLM,
    FakeStreamingSTT,
    FaultPlan,
)

from duplex_voice.audio.queue import InputAudioFrame
from duplex_voice.llm.base import (
    CancellationToken,
    LLMEventKind,
    Message,
    MessageRole,
    StreamingLLM,
)
from duplex_voice.providers.faults import (
    ProviderAdapterError,
    ProviderErrorCode,
    run_bounded,
)
from duplex_voice.stt.base import StreamingSTT, STTEventKind
from duplex_voice.tts.base import GenerationTTS, TTSEventKind
from duplex_voice.tts.generation_guard import GenerationGuard
from duplex_voice.tts.generation_state import GenerationToken


def _active_token() -> tuple[GenerationGuard, GenerationToken]:
    guard = GenerationGuard()
    token = guard.create("session-a")
    guard.activate(token)
    return guard, token


def test_fakes_conform_to_provider_protocols() -> None:
    guard, _ = _active_token()
    stt: StreamingSTT = FakeStreamingSTT()
    llm: StreamingLLM = FakeStreamingLLM(("一", "二"))
    tts: GenerationTTS = FakeGenerationTTS(guard)

    assert stt is not None
    assert llm is not None
    assert tts is not None


@pytest.mark.asyncio
async def test_stt_streams_revisions_while_accepting_audio() -> None:
    stt = FakeStreamingSTT()
    await stt.connect()
    await stt.push_audio(InputAudioFrame(1, b"pcm", 20, 1.0))
    await stt.emit_transcript("測", final=False, revision=1)
    await stt.emit_transcript("測試", final=True, revision=2)
    events = stt.events()

    partial = await anext(events)
    final = await anext(events)
    assert partial.kind is STTEventKind.PARTIAL_TRANSCRIPT
    assert partial.revision == 1
    assert final.kind is STTEventKind.FINAL_TRANSCRIPT
    assert final.revision == 2
    assert "測試" not in repr(final)
    await stt.close()


@pytest.mark.asyncio
async def test_llm_cancellation_stops_future_deltas() -> None:
    token = CancellationToken()
    llm = FakeStreamingLLM(("第一段", "第二段", "第三段"))
    events = llm.generate((Message(MessageRole.USER, "synthetic question"),), "generation-a", token)

    assert (await anext(events)).kind is LLMEventKind.REQUEST_STARTED
    assert (await anext(events)).kind is LLMEventKind.FIRST_TOKEN
    first_delta = await anext(events)
    token.cancel()
    cancelled = await anext(events)

    assert first_delta.kind is LLMEventKind.TEXT_DELTA
    assert cancelled.kind is LLMEventKind.CANCELLED
    with pytest.raises(StopAsyncIteration):
        await anext(events)


@pytest.mark.asyncio
async def test_tts_enforces_one_connection_per_generation_and_drops_late_audio() -> None:
    guard = GenerationGuard()
    first = guard.create("session-a")
    guard.activate(first)
    tts = FakeGenerationTTS(guard)
    await tts.connect(first)
    await tts.start_generation(first)
    assert await tts.emit_audio(first, b"audio", sequence=1)
    await tts.cancel_generation(first, "user_interruption")
    assert not await tts.emit_audio(first, b"late", sequence=2)

    second = guard.create("session-a")
    guard.activate(second)
    with pytest.raises(ProviderAdapterError, match="connection_reuse"):
        await tts.connect(second)


@pytest.mark.asyncio
async def test_provider_connect_timeout_is_bounded_and_redacted() -> None:
    stt = FakeStreamingSTT(FaultPlan(stall_connect=True))

    with pytest.raises(ProviderAdapterError) as exc_info:
        await run_bounded(
            stt.connect(),
            timeout_s=0.01,
            provider="fake_stt",
            operation_name="connect",
            trace_id="safe-trace",
            timeout_code=ProviderErrorCode.CONNECT_TIMEOUT,
        )

    assert exc_info.value.failure.code is ProviderErrorCode.CONNECT_TIMEOUT
    assert exc_info.value.failure.retryable
    assert "credential" not in str(exc_info.value).casefold()


@pytest.mark.asyncio
async def test_stt_fault_is_a_structured_event_not_an_unbounded_retry() -> None:
    stt = FakeStreamingSTT(FaultPlan(fail_after_items=1))
    await stt.connect()
    await stt.push_audio(InputAudioFrame(1, b"pcm", 20, 1.0))
    await stt.push_audio(InputAudioFrame(2, b"pcm", 20, 2.0))

    event = await anext(stt.events())
    assert event.kind is STTEventKind.ERROR
    assert event.error_code == "synthetic_failure"
    assert stt.received_frames == 2


@pytest.mark.asyncio
async def test_llm_fault_terminates_stream_with_safe_failure() -> None:
    llm = FakeStreamingLLM(("一", "二", "三"), FaultPlan(fail_after_items=1))
    events = [
        event
        async for event in llm.generate(
            (Message(MessageRole.USER, "private synthetic prompt"),),
            "generation-a",
            CancellationToken(),
        )
    ]

    assert [event.kind for event in events] == [
        LLMEventKind.REQUEST_STARTED,
        LLMEventKind.FIRST_TOKEN,
        LLMEventKind.TEXT_DELTA,
        LLMEventKind.FAILED,
    ]
    assert all("private synthetic prompt" not in repr(event) for event in events)


@pytest.mark.asyncio
async def test_tts_fault_emits_failure_and_never_stores_text_in_event_repr() -> None:
    guard = GenerationGuard()
    token = guard.create("session-a")
    guard.activate(token)
    tts = FakeGenerationTTS(guard, FaultPlan(fail_after_items=1))
    await tts.connect(token)
    await tts.start_generation(token)
    await tts.push_text(token, "private first text")
    await tts.push_text(token, "private second text")

    events = tts.events()
    seen = [await anext(events), await anext(events), await anext(events)]
    assert seen[-1].kind is TTSEventKind.REQUEST_FAILED
    assert all("private" not in repr(event) for event in seen)
    await tts.close()


@pytest.mark.asyncio
async def test_bounded_operation_returns_success_without_retry_layer() -> None:
    async def complete() -> str:
        await asyncio.sleep(0)
        return "ok"

    result = await run_bounded(
        complete(),
        timeout_s=1,
        provider="fake",
        operation_name="complete",
        trace_id="safe-trace",
        timeout_code=ProviderErrorCode.RECEIVE_TIMEOUT,
    )
    assert result == "ok"
