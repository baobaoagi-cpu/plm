"""Read-only Phase 3B admin contracts; no HTTP routes or mutations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from duplex_voice.calibration.persona_loader import CandidatePersonaManifest
from duplex_voice.calibration.staging_store import StagingIsolationStore


class AdminRoute(StrEnum):
    CONTROL_TOWER = "/"
    DATA_MAP = "/data-map"
    PERSONA = "/persona"
    SOUL_FOUNDRY = "/soul-foundry"


@dataclass(frozen=True, slots=True)
class ReadOnlyRouteContract:
    route: AdminRoute
    title: str
    method: str = "GET"
    mutation_allowed: bool = False


ADMIN_ROUTE_CONTRACTS = (
    ReadOnlyRouteContract(AdminRoute.CONTROL_TOWER, "控制塔"),
    ReadOnlyRouteContract(AdminRoute.DATA_MAP, "資料地圖"),
    ReadOnlyRouteContract(AdminRoute.PERSONA, "人格設定"),
    ReadOnlyRouteContract(AdminRoute.SOUL_FOUNDRY, "靈魂工坊"),
)


@dataclass(frozen=True, slots=True)
class ControlTowerSnapshot:
    environment: str
    tenant_id: str
    sandbox_enabled: bool
    production_connected: bool
    release_persona_present: bool
    counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class DataMapSnapshot:
    schema_name: str
    tables: tuple[str, ...]
    row_level_security_required: bool
    external_database_connected: bool


@dataclass(frozen=True, slots=True)
class PersonaSnapshot:
    persona_slug: str
    source_classification: str
    owner_confirmation_status: str
    candidate_count: int
    runtime_eligible: bool
    production_eligible: bool
    source_hash: str


@dataclass(frozen=True, slots=True)
class SoulFoundrySnapshot:
    candidate_count: int
    categories: tuple[str, ...]
    owner_decisions_recorded: int
    publish_allowed: bool


class StagingAdminReader:
    """Build immutable snapshots from in-process proof state."""

    def __init__(
        self,
        *,
        tenant_id: str,
        persona: CandidatePersonaManifest,
        store: StagingIsolationStore,
    ) -> None:
        self._tenant_id = tenant_id
        self._persona = persona
        self._store = store

    def control_tower(self) -> ControlTowerSnapshot:
        return ControlTowerSnapshot(
            environment="staging",
            tenant_id=self._tenant_id,
            sandbox_enabled=False,
            production_connected=False,
            release_persona_present=False,
            counts=tuple(sorted(self._store.safe_counts().items())),
        )

    def data_map(self) -> DataMapSnapshot:
        return DataMapSnapshot(
            schema_name="xiewenxian_staging",
            tables=(
                "tenants",
                "principals",
                "conversations",
                "student_memory",
                "prompt_log",
                "owner_evidence",
            ),
            row_level_security_required=True,
            external_database_connected=False,
        )

    def persona(self) -> PersonaSnapshot:
        return PersonaSnapshot(
            persona_slug=self._persona.persona_slug,
            source_classification=self._persona.source_classification,
            owner_confirmation_status=self._persona.owner_confirmation_status,
            candidate_count=len(self._persona.candidate_ids),
            runtime_eligible=self._persona.runtime_eligible,
            production_eligible=self._persona.production_eligible,
            source_hash=self._persona.file_sha256,
        )

    def soul_foundry(self) -> SoulFoundrySnapshot:
        return SoulFoundrySnapshot(
            candidate_count=len(self._persona.candidate_ids),
            categories=self._persona.categories,
            owner_decisions_recorded=0,
            publish_allowed=False,
        )


__all__ = [
    "ADMIN_ROUTE_CONTRACTS",
    "AdminRoute",
    "ControlTowerSnapshot",
    "DataMapSnapshot",
    "PersonaSnapshot",
    "ReadOnlyRouteContract",
    "SoulFoundrySnapshot",
    "StagingAdminReader",
]
