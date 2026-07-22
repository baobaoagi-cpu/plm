"""Bounded provider operations and redacted error mapping."""

from __future__ import annotations

import asyncio
import math
from collections.abc import Awaitable
from dataclasses import dataclass
from enum import StrEnum


class ProviderErrorCode(StrEnum):
    CONNECT_TIMEOUT = "connect_timeout"
    RECEIVE_TIMEOUT = "receive_timeout"
    AUTHENTICATION_FAILED = "authentication_failed"
    INVALID_CONFIGURATION = "invalid_configuration"
    RATE_LIMITED = "rate_limited"
    PROTOCOL_ERROR = "protocol_error"
    UNEXPECTED_CLOSE = "unexpected_close"
    CANCELLED = "cancelled"
    INTERNAL_ERROR = "internal_error"


@dataclass(frozen=True, slots=True)
class ProviderFailure:
    provider: str
    operation: str
    code: ProviderErrorCode
    retryable: bool
    trace_id: str


class ProviderAdapterError(RuntimeError):
    def __init__(self, failure: ProviderFailure) -> None:
        super().__init__(f"{failure.provider}:{failure.operation}:{failure.code.value}")
        self.failure = failure


async def run_bounded[T](
    operation: Awaitable[T],
    *,
    timeout_s: float,
    provider: str,
    operation_name: str,
    trace_id: str,
    timeout_code: ProviderErrorCode,
) -> T:
    if timeout_s <= 0 or not math.isfinite(timeout_s):
        raise ValueError("timeout_s must be finite and positive")
    try:
        return await asyncio.wait_for(operation, timeout=timeout_s)
    except TimeoutError:
        raise ProviderAdapterError(
            ProviderFailure(
                provider=provider,
                operation=operation_name,
                code=timeout_code,
                retryable=True,
                trace_id=trace_id,
            )
        ) from None


__all__ = [
    "ProviderAdapterError",
    "ProviderErrorCode",
    "ProviderFailure",
    "run_bounded",
]
