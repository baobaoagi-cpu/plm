"""Configuration boundary; provider validation is added with each implementation phase."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeDefaults:
    """Non-secret defaults explicitly specified by the development specification."""

    minimax_sample_rate: int = 24_000
    enable_interruption: bool = True
    min_overlap_ms: int = 180
    interruption_confirmation_ms: int = 300
    tts_max_pending_audio_ms: int = 2_000
    text_chunk_min_chars: int = 6
    text_chunk_preferred_chars: int = 16
    text_chunk_max_chars: int = 32
    text_chunk_max_wait_ms: int = 250
    enable_debug_events: bool = True
    enable_audio_dump: bool = False
