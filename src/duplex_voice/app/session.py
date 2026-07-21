"""Thread-safe call and transport lease registry with stale-release protection."""

from __future__ import annotations

import hashlib
import re
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass

_SAFE_OPAQUE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,191}$")


class SessionRegistryError(ValueError):
    """Raised when a lease cannot enter the registry safely."""


@dataclass(frozen=True, slots=True)
class TransportLease:
    effective_user_id: str
    call_id: str
    transport_id: str
    lease_id: str
    epoch: int
    opened_at_monotonic: float


@dataclass(frozen=True, slots=True)
class LeaseAcquisition:
    current: TransportLease
    superseded: TransportLease | None


class SessionRegistry:
    """Allow exactly one current call transport lease per effective principal."""

    def __init__(self, *, monotonic: Callable[[], float] = time.monotonic) -> None:
        self._monotonic = monotonic
        self._lock = threading.RLock()
        self._current_by_principal: dict[str, TransportLease] = {}
        self._epoch_by_principal: dict[str, int] = {}

    def acquire(
        self, effective_user_id: str, call_id: str, transport_id: str
    ) -> LeaseAcquisition:
        for name, value in (
            ("effective_user_id", effective_user_id),
            ("call_id", call_id),
            ("transport_id", transport_id),
        ):
            if not _SAFE_OPAQUE_ID.fullmatch(value):
                raise SessionRegistryError(f"{name} must be a bounded opaque identifier")

        with self._lock:
            previous = self._current_by_principal.get(effective_user_id)
            epoch = self._epoch_by_principal.get(effective_user_id, 0) + 1
            self._epoch_by_principal[effective_user_id] = epoch
            lease = TransportLease(
                effective_user_id=effective_user_id,
                call_id=call_id,
                transport_id=transport_id,
                lease_id=str(uuid.uuid4()),
                epoch=epoch,
                opened_at_monotonic=self._monotonic(),
            )
            self._current_by_principal[effective_user_id] = lease
            return LeaseAcquisition(current=lease, superseded=previous)

    def is_current(self, lease: TransportLease) -> bool:
        with self._lock:
            return self._current_by_principal.get(lease.effective_user_id) == lease

    def release(self, lease: TransportLease) -> bool:
        """Release only the exact current lease; stale cleanup cannot delete a replacement."""

        with self._lock:
            if self._current_by_principal.get(lease.effective_user_id) != lease:
                return False
            del self._current_by_principal[lease.effective_user_id]
            return True

    def current_for(self, effective_user_id: str) -> TransportLease | None:
        if not _SAFE_OPAQUE_ID.fullmatch(effective_user_id):
            raise SessionRegistryError(
                "effective_user_id must be a bounded opaque identifier"
            )
        with self._lock:
            return self._current_by_principal.get(effective_user_id)

    def snapshot(self) -> dict[str, object]:
        """Return counts and hashes only; never reveal effective user or call IDs."""

        with self._lock:
            leases = sorted(self._current_by_principal.values(), key=lambda item: item.lease_id)
            return {
                "active_lease_count": len(leases),
                "leases": [
                    {
                        "principal_fingerprint": hashlib.sha256(
                            lease.effective_user_id.encode()
                        ).hexdigest()[:12],
                        "call_fingerprint": hashlib.sha256(lease.call_id.encode()).hexdigest()[
                            :12
                        ],
                        "lease_id": lease.lease_id,
                        "epoch": lease.epoch,
                    }
                    for lease in leases
                ],
            }


__all__ = [
    "LeaseAcquisition",
    "SessionRegistry",
    "SessionRegistryError",
    "TransportLease",
]
