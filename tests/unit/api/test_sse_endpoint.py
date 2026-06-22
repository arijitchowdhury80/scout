"""Tests for the SSE streaming endpoint GET /app/runs/{run_id}/events/stream."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from scout.api.main import app

_HEADERS = {"X-API-Key": "dev-key"}


@pytest.fixture
def _override_crawler():
    """Provide a mock crawler so app startup doesn't need a real one."""
    from scout.api.deps import get_crawler

    mock = AsyncMock()
    app.dependency_overrides[get_crawler] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_crawler, None)


@pytest.fixture
def _patch_lifespan():
    """Bypass lifespan (no DB, no real crawler) for endpoint-only tests."""
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def noop_lifespan(_app):
        yield

    original = app.router.lifespan_context
    app.router.lifespan_context = noop_lifespan
    yield
    app.router.lifespan_context = original


@pytest.mark.asyncio
async def test_sse_404_for_unknown_run(_patch_lifespan) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/app/runs/nonexistent/events/stream", headers=_HEADERS)
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_sse_replays_historical_events(_patch_lifespan) -> None:
    """Create a run (inject into state), mark complete, stream should replay events and close."""
    from scout.api.routers.app_runs import AppRunEvent, AppRunState, _APP_RUNS

    run_id = "test_sse_replay"
    state = AppRunState(
        run_id=run_id,
        status="complete",
        use_case="products",
        mode="auto",
        events=[
            AppRunEvent(stage="queued", message="Run created"),
            AppRunEvent(stage="complete", message="Done"),
        ],
    )
    _APP_RUNS[run_id] = state
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/app/runs/{run_id}/events/stream", headers=_HEADERS)
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("text/event-stream")
            lines = resp.text.strip().split("\n")
            data_lines = [ln for ln in lines if ln.startswith("data: ")]
            assert len(data_lines) >= 2
            first = json.loads(data_lines[0].removeprefix("data: "))
            assert first["stage"] == "queued"
    finally:
        _APP_RUNS.pop(run_id, None)


@pytest.mark.asyncio
async def test_sse_streams_live_events(_patch_lifespan) -> None:
    """Start a run in 'running' status, publish events, verify they arrive via SSE."""
    from scout.api.routers.app_runs import (
        AppRunEvent,
        AppRunState,
        _APP_RUNS,
        _event_bus,
    )

    run_id = "test_sse_live"
    state = AppRunState(
        run_id=run_id,
        status="running",
        use_case="products",
        mode="auto",
        events=[AppRunEvent(stage="queued", message="Run created")],
    )
    _APP_RUNS[run_id] = state

    collected: list[str] = []

    async def consume_stream():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            async with client.stream(
                "GET", f"/app/runs/{run_id}/events/stream", headers=_HEADERS
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        collected.append(line.removeprefix("data: "))
                        parsed = json.loads(collected[-1])
                        if parsed.get("stage") == "close":
                            return

    consumer = asyncio.create_task(consume_stream())
    await asyncio.sleep(0.05)

    await _event_bus.publish(run_id, {"stage": "extracting", "message": "live event"})
    await _event_bus.publish(run_id, None)

    try:
        await asyncio.wait_for(consumer, timeout=3.0)
    except TimeoutError:
        consumer.cancel()

    _APP_RUNS.pop(run_id, None)

    data_events = [json.loads(d) for d in collected]
    stages = [e["stage"] for e in data_events]
    assert "queued" in stages
    assert "extracting" in stages


@pytest.mark.asyncio
async def test_sse_content_type(_patch_lifespan) -> None:
    from scout.api.routers.app_runs import AppRunEvent, AppRunState, _APP_RUNS

    run_id = "test_sse_ct"
    _APP_RUNS[run_id] = AppRunState(
        run_id=run_id,
        status="complete",
        use_case="products",
        mode="auto",
        events=[AppRunEvent(stage="complete", message="Done")],
    )
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/app/runs/{run_id}/events/stream", headers=_HEADERS)
            assert "text/event-stream" in resp.headers["content-type"]
    finally:
        _APP_RUNS.pop(run_id, None)
