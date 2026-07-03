"""Bounded in-process job queue for hosted Scout work."""

from __future__ import annotations

import asyncio
import inspect
import threading
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


HostedJobWork = Callable[[], Awaitable[Any] | Any]


class HostedQueueFull(Exception):
    """Raised when the hosted async queue cannot accept more work."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("Hosted job queue is full; retry shortly.")
        self.retry_after_seconds = retry_after_seconds


class HostedJobRecord(BaseModel):
    """Pollable state for an accepted hosted job."""

    job_id: str
    kind: str
    tenant_id: str
    key_id: str
    status: str = "queued"
    retry_after_seconds: int = 5
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    started_at: str = ""
    finished_at: str = ""
    result: dict[str, Any] | None = None
    error: str = ""


class HostedJobQueue:
    """Small bounded async worker queue for expensive hosted requests."""

    def __init__(self, *, max_queued: int, worker_count: int, retry_after_seconds: int = 5) -> None:
        self.max_queued = max(0, max_queued)
        self.worker_count = max(0, worker_count)
        self.retry_after_seconds = max(1, retry_after_seconds)
        self._jobs: dict[str, HostedJobRecord] = {}
        self._work: dict[str, HostedJobWork] = {}
        self._pending: list[str] = []
        self._tasks: list[asyncio.Task[None]] = []
        self._event: asyncio.Event | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start background workers in the current event loop."""
        if self.worker_count == 0 or self._tasks:
            return
        self._event = asyncio.Event()
        self._tasks = [asyncio.create_task(self._worker()) for _ in range(self.worker_count)]

    async def close(self) -> None:
        """Stop workers and wait for cancellation."""
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []

    def enqueue(
        self,
        *,
        kind: str,
        tenant_id: str,
        key_id: str,
        retry_after_seconds: int | None,
        work: HostedJobWork,
    ) -> HostedJobRecord:
        """Accept work for later execution or raise when the queue is full."""
        retry_after = retry_after_seconds or self.retry_after_seconds
        with self._lock:
            if self._queued_or_running_count() >= self.max_queued:
                raise HostedQueueFull(retry_after)
            job = HostedJobRecord(
                job_id=f"job_{uuid4().hex[:16]}",
                kind=kind,
                tenant_id=tenant_id,
                key_id=key_id,
                retry_after_seconds=retry_after,
            )
            self._jobs[job.job_id] = job
            self._work[job.job_id] = work
            self._pending.append(job.job_id)
        if self._event is not None:
            self._event.set()
        return job

    def get(self, job_id: str) -> HostedJobRecord | None:
        """Return job state if it is still retained in memory."""
        with self._lock:
            return self._jobs.get(job_id)

    def enqueue_sync_for_tests(
        self,
        *,
        kind: str,
        tenant_id: str,
        key_id: str,
        retry_after_seconds: int,
        work: HostedJobWork,
    ) -> HostedJobRecord:
        """Test helper for creating a queued job without HTTP routing."""
        return self.enqueue(
            kind=kind,
            tenant_id=tenant_id,
            key_id=key_id,
            retry_after_seconds=retry_after_seconds,
            work=work,
        )

    def run_next_sync_for_tests(self) -> HostedJobRecord | None:
        """Test helper that executes one pending job synchronously."""
        job_id = self._pop_next_job_id()
        if job_id is None:
            return None
        return asyncio.run(self._run_job(job_id))

    async def _worker(self) -> None:
        while True:
            job_id = self._pop_next_job_id()
            if job_id is None:
                assert self._event is not None
                self._event.clear()
                await self._event.wait()
                continue
            await self._run_job(job_id)

    async def _run_job(self, job_id: str) -> HostedJobRecord | None:
        with self._lock:
            job = self._jobs.get(job_id)
            work = self._work.get(job_id)
            if job is None or work is None:
                return job
            self._jobs[job_id] = job.model_copy(
                update={"status": "running", "started_at": datetime.now(UTC).isoformat()}
            )
        try:
            result = work()
            if inspect.isawaitable(result):
                result = await result
            update = {
                "status": "complete",
                "finished_at": datetime.now(UTC).isoformat(),
                "result": _serialize_result(result),
            }
        except Exception as exc:  # noqa: BLE001 - queue must preserve failures for polling.
            update = {
                "status": "failed",
                "finished_at": datetime.now(UTC).isoformat(),
                "error": str(exc),
            }
        with self._lock:
            job = self._jobs[job_id].model_copy(update=update)
            self._jobs[job_id] = job
            self._work.pop(job_id, None)
            return job

    def _pop_next_job_id(self) -> str | None:
        with self._lock:
            if not self._pending:
                return None
            return self._pending.pop(0)

    def _queued_or_running_count(self) -> int:
        return sum(1 for job in self._jobs.values() if job.status in {"queued", "running"})


def _serialize_result(result: Any) -> dict[str, Any]:
    if isinstance(result, BaseModel):
        return result.model_dump(mode="json")
    if isinstance(result, dict):
        return result
    return {"value": result}
