from duplex_voice import __version__
from duplex_voice.config import RuntimeDefaults


def test_package_imports() -> None:
    assert __version__ == "0.1.0"


def test_spec_defaults_are_safe() -> None:
    defaults = RuntimeDefaults()

    assert defaults.minimax_sample_rate == 24_000
    assert defaults.enable_interruption is True
    assert defaults.enable_audio_dump is False
    assert defaults.text_chunk_min_chars < defaults.text_chunk_preferred_chars
    assert defaults.text_chunk_preferred_chars < defaults.text_chunk_max_chars
