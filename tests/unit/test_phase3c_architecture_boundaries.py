from __future__ import annotations

import ast
from pathlib import Path

PHASE3C_RUNTIME_FILES = (
    Path("src/duplex_voice/api/protocol.py"),
    Path("src/duplex_voice/app/session.py"),
    Path("src/duplex_voice/audio/duplex_simulator.py"),
    Path("src/duplex_voice/audio/formats.py"),
    Path("src/duplex_voice/audio/queue.py"),
    Path("src/duplex_voice/calibration/identity_verifier.py"),
    Path("src/duplex_voice/llm/base.py"),
    Path("src/duplex_voice/providers/faults.py"),
    Path("src/duplex_voice/stt/base.py"),
    Path("src/duplex_voice/transports/base.py"),
    Path("src/duplex_voice/tts/base.py"),
)


def _imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".")[0])
    return roots


def test_phase3c_runtime_contracts_have_no_provider_or_orchestrator_sdk_imports() -> None:
    forbidden_roots = {
        "anthropic",
        "deepgram",
        "google",
        "linebot",
        "livekit",
        "mem0",
        "openai",
        "pipecat",
        "websockets",
    }

    for path in PHASE3C_RUNTIME_FILES:
        assert _imported_roots(path).isdisjoint(forbidden_roots), path


def test_formal_service_pipeline_and_livekit_transport_remain_unimplemented() -> None:
    placeholders = {
        Path("src/duplex_voice/tts/minimax_service.py"): "placeholder",
        Path("src/duplex_voice/app/pipeline_factory.py"): "placeholder",
        Path("src/duplex_voice/transports/livekit_transport.py"): "placeholder",
    }

    for path, required_marker in placeholders.items():
        source = path.read_text(encoding="utf-8").casefold()
        assert required_marker in source, path
        assert "class minimaxttsservice" not in source
        assert "pipeline(" not in source
        assert "agentsession" not in source


def test_runtime_contains_no_legacy_or_tracy_imports() -> None:
    forbidden_fragments = ("voice-pipeline", "voice_pipeline", "tracy", "livekit.agents")

    for path in Path("src").rglob("*.py"):
        source = path.read_text(encoding="utf-8").casefold()
        assert all(fragment not in source for fragment in forbidden_fragments), path
