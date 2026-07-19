from __future__ import annotations

import json
from pathlib import Path

from duplex_voice.calibration.identity import (
    SANDBOX_NOTICE,
    XIEWENXIAN_NAMESPACES,
    XIEWENXIAN_SECRET_SLOTS,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = PROJECT_ROOT / "docs" / "persona" / "xiewenxian" / "source"
WEB_DIR = PROJECT_ROOT / "web" / "src" / "xiewenxian-calibration"


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_candidate_register_stays_non_release_and_has_no_owner_quotes() -> None:
    register = _load_json(SOURCE_DIR / "xiewenxian-v2-candidate-register-v0.1.json")
    candidates = register["candidates"]
    assert isinstance(candidates, list)

    assert register["candidate_count"] == 46
    assert register["source_classification"] == (
        "PROJECT_OWNER_APPROVED_ENGINEERING_INTERPRETATION"
    )
    assert register["runtime_eligible"] is False
    assert register["production_eligible"] is False
    assert all(isinstance(item, dict) and item["status"] == "candidate" for item in candidates)
    assert all(
        isinstance(item, dict) and not str(item.get("owner_quote", "")).strip()
        for item in candidates
    )


def test_owner_confirmation_queue_has_no_recorded_decisions() -> None:
    queue = _load_json(SOURCE_DIR / "xiewenxian-owner-confirmation-queue-v0.1.json")
    items = queue["items"]
    assert isinstance(items, list)

    assert queue["item_count"] == 15
    assert queue["decisions_recorded"] == 0
    assert all(isinstance(item, dict) and item["decision"] is None for item in items)


def test_migration_inventory_pins_canonical_and_historical_sources() -> None:
    inventory = _load_json(
        PROJECT_ROOT / "docs" / "migration" / "xiewenxian-plm-migration-inventory.json"
    )
    historical = inventory["historical_source"]
    entries = inventory["entries"]
    assert isinstance(historical, dict)
    assert isinstance(entries, list)

    assert inventory["canonical_repository"] == "baobaoagi-cpu/plm"
    assert historical["commit"] == "a1ad3825cf17935622c158795dee019be99bcaaa"
    assert len(entries) == 31
    assert all(
        isinstance(item, dict)
        and {
            "classification",
            "target_path",
            "rewrite_required",
            "dependencies",
            "tenant_isolation",
            "test_requirements",
            "sensitive_data",
            "owner_confirmation_required",
        }.issubset(item)
        for item in entries
    )


def test_raw_v2_is_registered_but_explicitly_git_ignored() -> None:
    registration = (
        SOURCE_DIR / "xiewenxian-v2-source-registration-v0.1.md"
    ).read_text(encoding="utf-8")
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "5585cdde72525432729fc1ce2b15411ecf1e60d7df7b5fb19d785d0a620a817f" in registration
    assert "REFERENCE_ONLY" in registration
    raw_source_name = (
        "謝文憲 AI 分身"
        + "\N{FULLWIDTH VERTICAL LINE}"
        + "靈魂級核心主題提示詞 V2.md"
    )
    assert raw_source_name in gitignore


def test_calibration_identity_reserves_every_required_namespace() -> None:
    assert XIEWENXIAN_NAMESPACES.tenant_id == "xie_wenxian"
    assert XIEWENXIAN_NAMESPACES.persona_id == "xie_wenxian_owner_calibration_v0_1"
    assert XIEWENXIAN_NAMESPACES.memory_namespace == "xie_wenxian/calibration"
    assert XIEWENXIAN_NAMESPACES.mem0_user_id == "xie_wenxian/calibration/owner"
    assert XIEWENXIAN_NAMESPACES.audio_prefix == "xie_wenxian/calibration/audio"
    assert XIEWENXIAN_NAMESPACES.transcript_prefix == "xie_wenxian/calibration/transcripts"
    assert all(
        slot.startswith("XIEWENXIAN_CALIBRATION_")
        for slot in XIEWENXIAN_SECRET_SLOTS.values()
    )


def test_calibration_runtime_has_no_forbidden_orchestrator_imports() -> None:
    runtime_source = (
        PROJECT_ROOT / "src" / "duplex_voice" / "calibration" / "identity.py"
    ).read_text(encoding="utf-8").casefold()
    forbidden = (
        "from tracy",
        "import tracy",
        "voice_pipeline",
        "voice-pipeline",
        "connection_pool",
        "livekit.agents",
        "from mem0",
        "import mem0",
    )

    assert not any(pattern in runtime_source for pattern in forbidden)


def test_liff_shell_is_backend_free_disabled_and_sandbox_labelled() -> None:
    shell = (WEB_DIR / "CalibrationCallShell.tsx").read_text(encoding="utf-8")
    combined = "\n".join(path.read_text(encoding="utf-8") for path in WEB_DIR.glob("*.tsx"))

    assert SANDBOX_NOTICE in shell
    assert "callEnabled = false" in shell
    for forbidden in (
        "useAudio",
        "useWebSocket",
        "voice-pipeline",
        "minimax",
        "livekit",
        "@line/liff",
        "/avatar",
    ):
        assert forbidden.casefold() not in combined.casefold()


def test_no_formal_release_persona_was_created() -> None:
    assert not (PROJECT_ROOT / "docs" / "persona" / "xiewenxian" / "release").exists()
