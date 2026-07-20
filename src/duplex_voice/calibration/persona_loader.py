"""Fail-closed loader for the governed Xie Wenxian candidate register."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EXPECTED_SOURCE_CLASSIFICATION = "PROJECT_OWNER_APPROVED_ENGINEERING_INTERPRETATION"
EXPECTED_OWNER_CONFIRMATION_STATUS = "NOT_OWNER_CONFIRMED"
EXPECTED_PERSONA_SLUG = "xiewenxian"


class PersonaCandidateRejected(RuntimeError):
    """Raised when candidate material cannot safely enter the staging harness."""


@dataclass(frozen=True, slots=True)
class CandidatePersonaManifest:
    persona_slug: str
    source_id: str
    source_classification: str
    owner_confirmation_status: str
    candidate_ids: tuple[str, ...]
    categories: tuple[str, ...]
    file_sha256: str
    runtime_eligible: bool = False
    production_eligible: bool = False


class CandidatePersonaLoader:
    def __init__(self, approved_root: Path) -> None:
        try:
            self._approved_root = approved_root.resolve(strict=True)
        except OSError as exc:
            raise PersonaCandidateRejected("approved candidate root is unavailable") from exc

    def load(self, path: Path, *, expected_sha256: str) -> CandidatePersonaManifest:
        try:
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise PersonaCandidateRejected("candidate source is unavailable") from exc
        if not resolved.is_relative_to(self._approved_root):
            raise PersonaCandidateRejected("candidate source is outside the approved root")
        raw = resolved.read_bytes()
        actual_sha256 = hashlib.sha256(raw).hexdigest()
        if actual_sha256 != expected_sha256:
            raise PersonaCandidateRejected("candidate source hash mismatch")
        try:
            parsed = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PersonaCandidateRejected("candidate source must be valid UTF-8 JSON") from exc
        if not isinstance(parsed, dict):
            raise PersonaCandidateRejected("candidate register must be a JSON object")
        return self._validate(parsed, actual_sha256)

    @staticmethod
    def _validate(data: dict[str, Any], file_sha256: str) -> CandidatePersonaManifest:
        if data.get("persona_slug") != EXPECTED_PERSONA_SLUG:
            raise PersonaCandidateRejected("unexpected persona slug")
        if data.get("source_classification") != EXPECTED_SOURCE_CLASSIFICATION:
            raise PersonaCandidateRejected("candidate source classification is not approved")
        if data.get("owner_confirmation_status") != EXPECTED_OWNER_CONFIRMATION_STATUS:
            raise PersonaCandidateRejected("owner confirmation state is not the approved boundary")
        if data.get("runtime_eligible") is not False:
            raise PersonaCandidateRejected("candidate register must not be runtime eligible")
        if data.get("production_eligible") is not False:
            raise PersonaCandidateRejected("candidate register must not be production eligible")

        candidates = data.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise PersonaCandidateRejected("candidate register must contain candidates")
        if data.get("candidate_count") != len(candidates):
            raise PersonaCandidateRejected("candidate count does not match register contents")

        candidate_ids: list[str] = []
        categories: set[str] = set()
        for candidate in candidates:
            if not isinstance(candidate, dict):
                raise PersonaCandidateRejected("candidate entry must be an object")
            candidate_id = candidate.get("candidate_id")
            category = candidate.get("category")
            if not isinstance(candidate_id, str) or not candidate_id:
                raise PersonaCandidateRejected("candidate ID is missing")
            if not isinstance(category, str) or not category:
                raise PersonaCandidateRejected("candidate category is missing")
            if candidate.get("status") != "candidate":
                raise PersonaCandidateRejected("only candidate status is accepted")
            if str(candidate.get("owner_quote", "")).strip():
                raise PersonaCandidateRejected("unverified owner quote must remain empty")
            candidate_ids.append(candidate_id)
            categories.add(category)
        if len(candidate_ids) != len(set(candidate_ids)):
            raise PersonaCandidateRejected("candidate IDs must be unique")

        source_id = data.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise PersonaCandidateRejected("source ID is missing")
        return CandidatePersonaManifest(
            persona_slug=EXPECTED_PERSONA_SLUG,
            source_id=source_id,
            source_classification=EXPECTED_SOURCE_CLASSIFICATION,
            owner_confirmation_status=EXPECTED_OWNER_CONFIRMATION_STATUS,
            candidate_ids=tuple(candidate_ids),
            categories=tuple(sorted(categories)),
            file_sha256=file_sha256,
        )


__all__ = [
    "CandidatePersonaLoader",
    "CandidatePersonaManifest",
    "PersonaCandidateRejected",
]
