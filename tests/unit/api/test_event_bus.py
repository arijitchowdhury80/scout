"""Tests for EventBus — per-run async pub/sub for SSE streaming."""

from __future__ import annotations

import asyncio

import pytest

from scout.api.event_bus import EventBus


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


@pytest.mark.asyncio
async def test_publish_reaches_subscriber(bus: EventBus) -> None:
    queue = bus.subscribe("run_1")
    await bus.publish("run_1", {"stage": "extracting", "message": "hello"})
    event = queue.get_nowait()
    assert event == {"stage": "extracting", "message": "hello"}


@pytest.mark.asyncio
async def test_multiple_subscribers(bus: EventBus) -> None:
    q1 = bus.subscribe("run_1")
    q2 = bus.subscribe("run_1")
    await bus.publish("run_1", {"stage": "done"})
    assert q1.get_nowait() == {"stage": "done"}
    assert q2.get_nowait() == {"stage": "done"}


@pytest.mark.asyncio
async def test_publish_to_different_run_does_not_leak(bus: EventBus) -> None:
    q1 = bus.subscribe("run_1")
    q2 = bus.subscribe("run_2")
    await bus.publish("run_1", {"stage": "x"})
    assert q1.get_nowait() == {"stage": "x"}
    assert q2.empty()


@pytest.mark.asyncio
async def test_unsubscribe_stops_delivery(bus: EventBus) -> None:
    queue = bus.subscribe("run_1")
    bus.unsubscribe("run_1", queue)
    await bus.publish("run_1", {"stage": "after"})
    assert queue.empty()


@pytest.mark.asyncio
async def test_close_sends_sentinel(bus: EventBus) -> None:
    queue = bus.subscribe("run_1")
    await bus.close("run_1")
    sentinel = queue.get_nowait()
    assert sentinel is None


@pytest.mark.asyncio
async def test_close_clears_subscribers(bus: EventBus) -> None:
    bus.subscribe("run_1")
    await bus.close("run_1")
    assert bus.subscriber_count("run_1") == 0


@pytest.mark.asyncio
async def test_publish_no_subscribers_is_noop(bus: EventBus) -> None:
    await bus.publish("nonexistent", {"stage": "x"})


@pytest.mark.asyncio
async def test_unsubscribe_unknown_queue_is_noop(bus: EventBus) -> None:
    other_queue: asyncio.Queue[dict | None] = asyncio.Queue()
    bus.unsubscribe("run_1", other_queue)


@pytest.mark.asyncio
async def test_subscriber_count(bus: EventBus) -> None:
    assert bus.subscriber_count("run_1") == 0
    bus.subscribe("run_1")
    assert bus.subscriber_count("run_1") == 1
    q2 = bus.subscribe("run_1")
    assert bus.subscriber_count("run_1") == 2
    bus.unsubscribe("run_1", q2)
    assert bus.subscriber_count("run_1") == 1
