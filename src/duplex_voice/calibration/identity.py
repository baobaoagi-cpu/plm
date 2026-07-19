"""Fail-closed identity policy for an owner-only persona calibration sandbox.

This module contains no LINE, model, TTS, memory, or storage integration.  It only
defines the identity and namespace bindings that those adapters must satisfy in
later, separately approved milestones.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from os import environ

SANDBOX_NOTICE = (
    "目前為本人校準測試版本。內容尚未代表謝文憲老師正式立場。"
)
XIEWENXIAN_SECRET_SLOT_PREFIX = "XIEWENXIAN_CALIBRATION_"


class CalibrationRole(StrEnum):
    OWNER = "OWNER"
    GOVERNOR = "GOVERNOR"
    TECHNICAL_TESTER = "TECHNICAL_TESTER"
    DENIED = "DENIED"


class CalibrationPermission(StrEnum):
    INTERACT = "INTERACT"
    SUBMIT_OWNER_EVIDENCE = "SUBMIT_OWNER_EVIDENCE"
    GOVERN = "GOVERN"
    TECHNICAL_TEST = "TECHNICAL_TEST"


class CalibrationAccessDenied(PermissionError):
    """Raised when the sandbox must not generate a response."""


@dataclass(frozen=True, slots=True)
class NamespaceBinding:
    tenant_id: str
    persona_id: str
    persona_version_binding: str
    memory_namespace: str
    mem0_user_id: str
    database_tenant: str
    audio_prefix: str
    transcript_prefix: str
    livekit_room_namespace: str
    prompt_cache_namespace: str
    session_state_namespace: str

    def values(self) -> tuple[str, ...]:
        return (
            self.tenant_id,
            self.persona_id,
            self.persona_version_binding,
            self.memory_namespace,
            self.mem0_user_id,
            self.database_tenant,
            self.audio_prefix,
            self.transcript_prefix,
            self.livekit_room_namespace,
            self.prompt_cache_namespace,
            self.session_state_namespace,
        )

    def assert_disjoint_from(self, other: NamespaceBinding) -> None:
        overlap = set(self.values()).intersection(other.values())
        if overlap:
            raise ValueError(f"校準命名空間不得共用: {', '.join(sorted(overlap))}")


@dataclass(frozen=True, slots=True)
class SecretSlotBinding:
    line_channel_id: str
    line_channel_secret: str
    line_channel_access_token: str
    liff_id: str
    minimax_voice_id: str
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str

    def validate(self) -> None:
        slots = self.values()
        if len(set(slots)) != len(slots):
            raise ValueError("謝文憲校準環境的秘密設定槽不得重複")
        if not all(slot.startswith(XIEWENXIAN_SECRET_SLOT_PREFIX) for slot in slots):
            raise ValueError("秘密設定槽必須使用謝文憲校準環境專屬前綴")

    def values(self) -> tuple[str, ...]:
        return (
            self.line_channel_id,
            self.line_channel_secret,
            self.line_channel_access_token,
            self.liff_id,
            self.minimax_voice_id,
            self.livekit_url,
            self.livekit_api_key,
            self.livekit_api_secret,
        )


XIEWENXIAN_NAMESPACES = NamespaceBinding(
    tenant_id="xie_wenxian",
    persona_id="xie_wenxian_owner_calibration_v0_1",
    persona_version_binding="xiewenxian-v2-candidate-register-v0.1",
    memory_namespace="xie_wenxian/calibration",
    mem0_user_id="xie_wenxian/calibration/owner",
    database_tenant="xie_wenxian",
    audio_prefix="xie_wenxian/calibration/audio",
    transcript_prefix="xie_wenxian/calibration/transcripts",
    livekit_room_namespace="xie_wenxian/calibration/livekit",
    prompt_cache_namespace="xie_wenxian/calibration/prompt-cache",
    session_state_namespace="xie_wenxian/calibration/session-state",
)

XIEWENXIAN_SECRET_SLOTS = SecretSlotBinding(
    line_channel_id="XIEWENXIAN_CALIBRATION_LINE_CHANNEL_ID",
    line_channel_secret="XIEWENXIAN_CALIBRATION_LINE_CHANNEL_SECRET",
    line_channel_access_token="XIEWENXIAN_CALIBRATION_LINE_CHANNEL_ACCESS_TOKEN",
    liff_id="XIEWENXIAN_CALIBRATION_LIFF_ID",
    minimax_voice_id="XIEWENXIAN_CALIBRATION_MINIMAX_VOICE_ID",
    livekit_url="XIEWENXIAN_CALIBRATION_LIVEKIT_URL",
    livekit_api_key="XIEWENXIAN_CALIBRATION_LIVEKIT_API_KEY",
    livekit_api_secret="XIEWENXIAN_CALIBRATION_LIVEKIT_API_SECRET",
)


@dataclass(frozen=True, slots=True)
class AccessDecision:
    allowed: bool
    role: CalibrationRole
    reason: str
    may_create_owner_evidence: bool


@dataclass(frozen=True, slots=True)
class OwnerCalibrationPolicy:
    roles_by_line_user_id: Mapping[str, CalibrationRole]
    enabled: bool = False
    kill_switch: bool = True
    sandbox_mode: bool = True
    namespaces: NamespaceBinding = XIEWENXIAN_NAMESPACES
    secret_slots: SecretSlotBinding = XIEWENXIAN_SECRET_SLOTS

    def __post_init__(self) -> None:
        if not self.sandbox_mode:
            raise ValueError("本人校準環境不得關閉 sandbox mode")
        self.secret_slots.validate()
        for user_id in self.roles_by_line_user_id:
            if not user_id.startswith("U"):
                raise ValueError("LINE allowlist 僅接受原始一對一 LINE User ID")

    def authorize(
        self,
        line_user_id: str,
        permission: CalibrationPermission = CalibrationPermission.INTERACT,
    ) -> AccessDecision:
        role = self.roles_by_line_user_id.get(line_user_id, CalibrationRole.DENIED)
        if not self.enabled:
            return AccessDecision(False, role, "sandbox_disabled", False)
        if self.kill_switch:
            return AccessDecision(False, role, "kill_switch_active", False)
        if role is CalibrationRole.DENIED:
            return AccessDecision(False, role, "line_user_not_allowlisted", False)

        allowed_permissions = {
            CalibrationRole.OWNER: {
                CalibrationPermission.INTERACT,
                CalibrationPermission.SUBMIT_OWNER_EVIDENCE,
            },
            CalibrationRole.GOVERNOR: {
                CalibrationPermission.INTERACT,
                CalibrationPermission.GOVERN,
            },
            CalibrationRole.TECHNICAL_TESTER: {
                CalibrationPermission.INTERACT,
                CalibrationPermission.TECHNICAL_TEST,
            },
            CalibrationRole.DENIED: set(),
        }
        allowed = permission in allowed_permissions[role]
        return AccessDecision(
            allowed=allowed,
            role=role,
            reason="allowed" if allowed else "role_permission_denied",
            may_create_owner_evidence=(
                allowed and permission is CalibrationPermission.SUBMIT_OWNER_EVIDENCE
            ),
        )

    def require_response_allowed(self, line_user_id: str) -> CalibrationRole:
        decision = self.authorize(line_user_id)
        if not decision.allowed:
            raise CalibrationAccessDenied(decision.reason)
        return decision.role

    def decorate_sandbox_response(self, response: str) -> str:
        return f"【本人校準版】{SANDBOX_NOTICE}\n\n{response.strip()}"


def _read_bool(raw: str | None, *, default: bool) -> bool:
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError("布林環境變數只能使用 true/false、1/0、yes/no 或 on/off")


def parse_line_allowlist(raw: str) -> dict[str, CalibrationRole]:
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("XIEWENXIAN_CALIBRATION_LINE_ALLOWLIST_JSON 必須是 JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("LINE allowlist 必須是 user ID 到角色的 JSON object")

    roles: dict[str, CalibrationRole] = {}
    for user_id, raw_role in parsed.items():
        if not isinstance(user_id, str) or not isinstance(raw_role, str):
            raise ValueError("LINE allowlist 的 user ID 與角色必須是字串")
        try:
            roles[user_id] = CalibrationRole(raw_role)
        except ValueError as exc:
            raise ValueError(f"不支援的校準角色: {raw_role}") from exc
    return roles


def load_owner_calibration_policy(
    environment: Mapping[str, str] = environ,
) -> OwnerCalibrationPolicy:
    """Load non-secret policy switches and an env-only LINE allowlist."""
    return OwnerCalibrationPolicy(
        roles_by_line_user_id=parse_line_allowlist(
            environment.get("XIEWENXIAN_CALIBRATION_LINE_ALLOWLIST_JSON", "")
        ),
        enabled=_read_bool(
            environment.get("XIEWENXIAN_CALIBRATION_ENABLED"), default=False
        ),
        kill_switch=_read_bool(
            environment.get("XIEWENXIAN_CALIBRATION_KILL_SWITCH"), default=True
        ),
        sandbox_mode=_read_bool(
            environment.get("XIEWENXIAN_CALIBRATION_SANDBOX_MODE"), default=True
        ),
    )
