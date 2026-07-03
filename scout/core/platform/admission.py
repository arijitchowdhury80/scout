"""Small process-local admission controller for expensive hosted work."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import asyncio
import time


class AdmissionRejected(Exception):
    """Raised when no worker capacity is currently available."""

    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__("Worker capacity is full; retry shortly.")


class AdmissionController:
    """Bound concurrent expensive work inside one Scout API process."""

    def __init__(self, max_active: int, retry_after_seconds: int = 5) -> None:
        self.max_active = max(0, max_active)
        self.retry_after_seconds = max(1, retry_after_seconds)
        self._active = 0
        self._reject_until = 0.0
        self._lock = asyncio.Lock()

    @property
    def active(self) -> int:
        return self._active

    @asynccontextmanager
    async def admit(self) -> AsyncIterator[None]:
        async with self._lock:
            now = time.monotonic()
            if now < self._reject_until or self._active >= self.max_active:
                self._reject_until = now + self.retry_after_seconds
                raise AdmissionRejected(self.retry_after_seconds)
            self._active += 1
        try:
            yield
        finally:
            async with self._lock:
                self._active = max(0, self._active - 1)
