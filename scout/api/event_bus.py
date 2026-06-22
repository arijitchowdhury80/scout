"""Per-run async pub/sub for SSE streaming."""

from __future__ import annotations

import asyncio
from typing import Any


class EventBus:
    """Fan-out event bus keyed by run_id.

    Each subscriber gets an ``asyncio.Queue``.  ``publish()`` pushes to every
    queue for that run.  ``close()`` sends a ``None`` sentinel so consumers
    know the stream is done, then removes all subscribers for that run.
    """

    def __init__(self) -> None:
        self._subs: dict[str, list[asyncio.Queue[dict[str, Any] | None]]] = {}

    def subscribe(self, run_id: str) -> asyncio.Queue[dict[str, Any] | None]:
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        self._subs.setdefault(run_id, []).append(queue)
        return queue

    def unsubscribe(self, run_id: str, queue: asyncio.Queue[dict[str, Any] | None]) -> None:
        queues = self._subs.get(run_id, [])
        try:
            queues.remove(queue)
        except ValueError:
            pass

    async def publish(self, run_id: str, event: dict[str, Any] | None) -> None:
        for queue in self._subs.get(run_id, []):
            await queue.put(event)

    async def close(self, run_id: str) -> None:
        for queue in self._subs.get(run_id, []):
            await queue.put(None)
        self._subs.pop(run_id, None)

    def subscriber_count(self, run_id: str) -> int:
        return len(self._subs.get(run_id, []))
