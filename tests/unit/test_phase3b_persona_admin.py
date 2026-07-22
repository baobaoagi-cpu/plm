from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from duplex_voice.calibration.admin_contracts import (
    ADMIN_ROUTE_CONTRACTS,
    AdminRoute,
    StagingAdminReader,
)
from duplex_voice.calibration.persona_loader import (
    CandidatePersonaLoader,
    CandidatePersonaManifest,
    PersonaCandidateRejected,
)
from duplex_voice.calibration.staging_store import StagingIsolationStore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = PROJECT_ROOT / "docs" / "persona" / "xiewenxian" / "source"
CANDIDATE_PATH = SOURCE_DIR / "xiewenxian-v2-candidate-register-v0.1.json"
CANDIDATE_SHA256 = "565ea160992c06c8de24e814be4b8316eda668ef2b99dec8521c6c7f2415773e"


def _load_real_manifest() -> CandidatePersonaManifest:
    return CandidatePersonaLoader(SOURCE_DIR).load(
        CANDIDATE_PATH, expected_sha256=CANDIDATE_SHA256
    )


def _write_register(root: Path, register: dict[str, Any]) -> tuple[Path, str]:
    path = root / "candidate.json"
    raw = json.dumps(register, ensure_ascii=False).encode()
    path.write_bytes(raw)
    return path, hashlib.sha256(raw).hexdigest()


def test_real_candidate_register_loads_as_non_release_manifest() -> None:
    manifest = _load_real_manifest()

    assert manifest.persona_slug == "xiewenxian"
    assert manifest.source_classification == (
        "PROJECT_OWNER_APPROVED_ENGINEERING_INTERPRETATION"
    )
    assert manifest.owner_confirmation_status == "NOT_OWNER_CONFIRMED"
    assert len(manifest.candidate_ids) == 46
    assert manifest.runtime_eligible is False
    assert manifest.production_eligible is False


def test_candidate_loader_rejects_wrong_hash() -> None:
    with pytest.raises(PersonaCandidateRejected, match="hash mismatch"):
        CandidatePersonaLoader(SOURCE_DIR).load(
            CANDIDATE_PATH, expected_sha256="0" * 64
        )


def test_candidate_loader_rejects_missing_source(tmp_path: Path) -> None:
    with pytest.raises(PersonaCandidateRejected, match="source is unavailable"):
        CandidatePersonaLoader(tmp_path).load(
            tmp_path / "missing.json", expected_sha256="0" * 64
        )


def test_candidate_loader_rejects_source_outside_approved_root(tmp_path: Path) -> None:
    with pytest.raises(PersonaCandidateRejected, match="outside the approved root"):
        CandidatePersonaLoader(tmp_path).load(
            CANDIDATE_PATH, expected_sha256=CANDIDATE_SHA256
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (("runtime_eligible", True), "runtime eligible"),
        (("production_eligible", True), "production eligible"),
        (("persona_slug", "other_persona"), "unexpected persona"),
        (("owner_confirmation_status", "OWNER_CONFIRMED"), "owner confirmation"),
    ],
)
def test_candidate_loader_rejects_governance_boundary_changes(
    tmp_path: Path, mutation: tuple[str, object], message: str
) -> None:
    register = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
    assert isinstance(register, dict)
    register[mutation[0]] = mutation[1]
    path, digest = _write_register(tmp_path, register)

    with pytest.raises(PersonaCandidateRejected, match=message):
        CandidatePersonaLoader(tmp_path).load(path, expected_sha256=digest)


def test_candidate_loader_rejects_unverified_owner_quote(tmp_path: Path) -> None:
    register = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
    assert isinstance(register, dict)
    candidates = register["candidates"]
    assert isinstance(candidates, list) and isinstance(candidates[0], dict)
    candidates[0]["owner_quote"] = "synthetic unverified quote"
    path, digest = _write_register(tmp_path, register)

    with pytest.raises(PersonaCandidateRejected, match="owner quote"):
        CandidatePersonaLoader(tmp_path).load(path, expected_sha256=digest)


def test_admin_contracts_are_exactly_four_get_only_routes() -> None:
    assert {contract.route for contract in ADMIN_ROUTE_CONTRACTS} == {
        AdminRoute.CONTROL_TOWER,
        AdminRoute.DATA_MAP,
        AdminRoute.PERSONA,
        AdminRoute.SOUL_FOUNDRY,
    }
    assert all(contract.method == "GET" for contract in ADMIN_ROUTE_CONTRACTS)
    assert all(contract.mutation_allowed is False for contract in ADMIN_ROUTE_CONTRACTS)


def test_admin_snapshots_report_staging_truth_and_cannot_publish() -> None:
    reader = StagingAdminReader(
        tenant_id="xie_wenxian",
        persona=_load_real_manifest(),
        store=StagingIsolationStore(),
    )

    control = reader.control_tower()
    data_map = reader.data_map()
    persona = reader.persona()
    foundry = reader.soul_foundry()

    assert control.environment == "staging"
    assert control.production_connected is False
    assert control.release_persona_present is False
    assert data_map.row_level_security_required is True
    assert data_map.external_database_connected is False
    assert persona.candidate_count == 46
    assert persona.runtime_eligible is False
    assert persona.production_eligible is False
    assert foundry.owner_decisions_recorded == 0
    assert foundry.publish_allowed is False
    with pytest.raises(FrozenInstanceError):
        control.production_connected = True  # type: ignore[misc]
