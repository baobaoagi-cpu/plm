from __future__ import annotations

import asyncio
import json
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from duplex_voice.app.session import SessionRegistry, SessionRegistryError, TransportLease


def test_reconnect_supersedes_old_lease_and_stale_cleanup_cannot_delete_new() -> None:
    registry = SessionRegistry()
    first = registry.acquire("xie_wenxian:synthetic:a", "call-1", "transport-1")
    second = registry.acquire("xie_wenxian:synthetic:a", "call-2", "transport-2")

    assert second.superseded == first.current
    assert not registry.is_current(first.current)
    assert registry.is_current(second.current)
    assert not registry.release(first.current)
    assert registry.current_for("xie_wenxian:synthetic:a") == second.current
    assert registry.release(second.current)
    assert not registry.release(second.current)


def test_different_principals_have_independent_leases() -> None:
    registry = SessionRegistry()
    first = registry.acquire("xie_wenxian:synthetic:a", "call-a", "transport-a")
    second = registry.acquire("xie_wenxian:synthetic:b", "call-b", "transport-b")

    assert registry.is_current(first.current)
    assert registry.is_current(second.current)
    assert registry.snapshot()["active_lease_count"] == 2


def test_snapshot_hashes_identifiers() -> None:
    registry = SessionRegistry()
    principal = "xie_wenxian:synthetic:private-principal"
    call_id = "private-call"
    registry.acquire(principal, call_id, "transport-a")

    rendered = json.dumps(registry.snapshot())
    assert principal not in rendered
    assert call_id not in rendered
    assert "transport-a" not in rendered


@pytest.mark.parametrize("value", ["", "has whitespace", "/path", "a" * 193])
def test_unsafe_identifiers_fail_closed(value: str) -> None:
    registry = SessionRegistry()

    with pytest.raises(SessionRegistryError, match="bounded opaque"):
        registry.acquire(value, "call-a", "transport-a")


@pytest.mark.asyncio
async def test_concurrent_reconnect_leaves_exactly_one_current_lease() -> None:
    registry = SessionRegistry()
    worker_count = 20
    barrier = threading.Barrier(worker_count)

    def acquire(index: int) -> TransportLease:
        barrier.wait()
        return registry.acquire(
            "xie_wenxian:synthetic:a", f"call-{index}", f"transport-{index}"
        ).current

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        leases = await asyncio.gather(
            *(loop.run_in_executor(executor, acquire, index) for index in range(worker_count))
        )

    assert sum(registry.is_current(lease) for lease in leases) == 1
    assert registry.snapshot()["active_lease_count"] == 1
    assert {lease.epoch for lease in leases} == set(range(1, worker_count + 1))
