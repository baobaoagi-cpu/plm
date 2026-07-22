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
    assert all(value is False for value in states.values())
    assert boundary["railway_liff_id_injected"] is False
    assert boundary["runtime_configuration_activated"] is False
    assert boundary["credentials_added"] is False


def test_unverified_liff_settings_are_not_promoted_to_verified() -> None:
    contract = _load_contract()
    settings = contract["registration_settings"]
    verification = contract["verification"]
    assert isinstance(settings, dict)
    assert isinstance(verification, dict)
    assert all(value != "VERIFIED" for value in settings.values())
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
