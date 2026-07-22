"""Contract for provider verification before identity mapping."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from duplex_voice.calibration.identity_mapping import VerifiedIdentityAssertion


@dataclass(frozen=True, slots=True)
class OpaqueCredential:
    value: str = field(repr=False)

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("credential must not be empty")


class IdentityVerifier(Protocol):
    async def verify(self, credential: OpaqueCredential) -> VerifiedIdentityAssertion: ...


__all__ = ["IdentityVerifier", "OpaqueCredential"]
