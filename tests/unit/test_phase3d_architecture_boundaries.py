from __future__ import annotations

import ast
from pathlib import Path

PHASE3D_PYTHON = (
    Path("src/duplex_voice/api/call_grant.py"),
    Path("src/duplex_voice/api/ingress.py"),
    Path("src/duplex_voice/observability/event_log.py"),
    Path("src/duplex_voice/observability/metrics.py"),
)
PHASE3D_WEB = Path("web/src/xiewenxian-calibration/offline")


def _imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".")[0])
    return roots


def test_phase3d_python_has_no_provider_transport_or_orchestrator_sdk() -> None:
    forbidden = {
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
    for path in PHASE3D_PYTHON:
        assert _imported_roots(path).isdisjoint(forbidden), path


def test_phase3d_browser_lab_has_no_network_or_provider_client() -> None:
    forbidden = (
        "fetch(",
        "new websocket",
        "livekit",
        "minimax",
        "deepgram",
        "getusermedia(",
        "authorization",
    )
    for path in PHASE3D_WEB.glob("*.ts"):
        source = path.read_text(encoding="utf-8").casefold()
        assert all(fragment not in source for fragment in forbidden), path


def test_phase3d_does_not_implement_formal_runtime_boundaries() -> None:
    source = "\n".join(path.read_text(encoding="utf-8").casefold() for path in PHASE3D_PYTHON)
    assert "minimaxttsservice" not in source
    assert "pipeline(" not in source
    assert "agentsession" not in source
    assert "connectionpool" not in source
