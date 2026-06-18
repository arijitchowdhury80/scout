"""WebSocket bridge for the embedded browser (the backend door the UI + other
apps ride on). Message routing is pure and unit-tested with a fake session;
auth is enforced in-handler (Starlette middleware doesn't cover websockets).
"""

import asyncio

from fastapi.testclient import TestClient

from scout.api.main import app
from scout.api.routers.live_browser import handle_client_message


class FakeSession:
    def __init__(self) -> None:
        self.dispatched: list = []
        self.navigated: str | None = None

    async def dispatch(self, event) -> None:
        self.dispatched.append(event)

    async def navigate(self, url) -> None:
        self.navigated = url

    async def snapshot(self):
        return ("https://t/", "Title", "<html>" + "x" * 80 + "</html>")


def _run(coro):
    return asyncio.run(coro)


def test_input_message_dispatches_event() -> None:
    s = FakeSession()
    resp = _run(handle_client_message(s, {"kind": "input", "event": {"type": "mousedown", "x": 1, "y": 2}}))
    assert resp is None
    assert s.dispatched == [{"type": "mousedown", "x": 1, "y": 2}]


def test_navigate_message_routes_and_acks() -> None:
    s = FakeSession()
    resp = _run(handle_client_message(s, {"kind": "navigate", "url": "https://x/"}))
    assert s.navigated == "https://x/"
    assert resp["kind"] == "navigated"
    assert resp["url"] == "https://x/"


def test_snapshot_message_returns_page_summary() -> None:
    s = FakeSession()
    resp = _run(handle_client_message(s, {"kind": "snapshot"}))
    assert resp["kind"] == "snapshot"
    assert resp["title"] == "Title"
    assert resp["url"] == "https://t/"


def test_unknown_kind_returns_error() -> None:
    s = FakeSession()
    resp = _run(handle_client_message(s, {"kind": "frobnicate"}))
    assert resp["kind"] == "error"


def test_ws_rejects_missing_or_wrong_key() -> None:
    client = TestClient(app)
    with client.websocket_connect("/app/live?key=wrong&url=about:blank") as ws:
        data = ws.receive_json()
    assert data["kind"] == "error"
    assert "unauthor" in data["message"].lower()
