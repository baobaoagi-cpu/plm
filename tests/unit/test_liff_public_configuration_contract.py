from __future__ import annotations

import json
from pathlib import Path
from typing import cast

CONTRACT_PATH = Path("docs/specs/liff-staging-public-configuration-v1.json")


def _load_contract() -> dict[str, object]:
    return cast(
        dict[str, object], json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    )


def test_liff_registration_values_are_public_config_only() -> None:
    contract = _load_contract()
    classification = contract["value_classification"]
    assert isinstance(classification, dict)
    assert set(classification.values()) == {"PUBLIC_CONFIG"}


def test_liff_registration_does_not_activate_integrations() -> None:
    contract = _load_contract()
    states = contract["integration_states"]
    boundary = contract["activation_boundary"]
    assert isinstance(states, dict)
    assert isinstance(boundary, dict)
    assert states["liff_sdk_adapter_implemented"] is True
    assert states["server_verification_boundary_implemented"] is True
    assert states["offline_verification_complete"] is True
    runtime_states = {
        name: value
        for name, value in states.items()
        if name
        not in {
            "liff_sdk_adapter_implemented",
            "server_verification_boundary_implemented",
            "offline_verification_complete",
        }
    }
    assert all(value is False for value in runtime_states.values())
    assert boundary["railway_liff_id_injected"] == "STAGED_NO_DEPLOY"
    assert boundary["runtime_configuration_activated"] is False
    assert boundary["credentials_added"] is False


def test_human_verified_settings_do_not_promote_line_identity() -> None:
    contract = _load_contract()
    settings = contract["registration_settings"]
    verification = contract["verification"]
    assert isinstance(settings, dict)
    assert isinstance(verification, dict)
    assert settings == {
        "openid_scope": "HUMAN_SCREENSHOT_VERIFIED_ENABLED",
        "profile_scope": "HUMAN_SCREENSHOT_VERIFIED_DISABLED",
        "chat_message_write_scope": "HUMAN_SCREENSHOT_VERIFIED_DISABLED",
        "add_friend_option": "HUMAN_SCREENSHOT_VERIFIED_OFF",
        "scan_qr_option": "HUMAN_SCREENSHOT_VERIFIED_OFF",
        "module_mode": "HUMAN_SCREENSHOT_VERIFIED_OFF",
        "share_target_picker": "HUMAN_SCREENSHOT_VERIFIED_OFF",
    }
    assert verification["line_identity"] == "NOT_VERIFIED"
    assert verification["real_user_authentication"] == "NOT_EXECUTED"


def test_public_contract_contains_no_credential_fields() -> None:
    serialized = CONTRACT_PATH.read_text(encoding="utf-8").casefold()
    forbidden = (
        "channel_secret",
        "channel_access_token",
        "authorization",
        "api_key",
        "voice_id",
    )
    assert all(name not in serialized for name in forbidden)
