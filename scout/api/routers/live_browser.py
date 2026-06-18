"""WebSocket bridge for the embedded browser pane.

Streams a live Chromium session's frames to the Scout UI (or any embedding app)
and forwards the client's input back in. This is the backend door behind the
embedded browser; the UI canvas and programmatic embedders both connect here.

Auth is enforced in-handler: Starlette's BaseHTTPMiddleware does not run for
websocket scopes, so the X-API-Key middleware never sees this route. The key is
passed as a query param (browsers can't set headers on a WebSocket).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from scout.api.config import settings
from scout.api.live_browser_page import live_browser_page_html
from scout.core.live_browser import LiveBrowserSession

router = APIRouter(tags=["live-browser"])


@router.get("/app/live-browser", response_class=HTMLResponse, include_in_schema=False)
async def live_browser_console() -> str:
    """The embedded-browser console page (canvas streamed from /app/live)."""
    return live_browser_page_html(settings.scout_api_key)

# Embedded browser runs headless and is streamed into the UI (no popup window).
_HEADLESS = True


def _make_session() -> LiveBrowserSession:
    """Session factory — overridable in tests so no real browser launches."""
    return LiveBrowserSession()


async def handle_client_message(session: Any, msg: dict[str, Any]) -> dict[str, Any] | None:
    """Route one inbound client message to the live session.

    Returns a dict to send back to the client, or None when nothing is owed
    (e.g. fire-and-forget input). Pure routing — unit-tested with a fake session.
    """
    kind = msg.get("kind")

    if kind == "input":
        await session.dispatch(msg.get("event", {}))
        return None

    if kind == "navigate":
        url = msg.get("url", "")
        await session.navigate(url)
        return {"kind": "navigated", "url": url}

    if kind == "snapshot":
        url, title, html = await session.snapshot()
        return {"kind": "snapshot", "url": url, "title": title, "chars": len(html)}

    return {"kind": "error", "message": f"unknown message kind: {kind!r}"}


@router.websocket("/app/live")
async def live_browser_ws(websocket: WebSocket, key: str = "", url: str = "") -> None:
    """Embedded-browser bridge: frames out, input in, over one WebSocket."""
    await websocket.accept()

    if key != settings.scout_api_key:
        await websocket.send_json({"kind": "error", "message": "unauthorized"})
        await websocket.close(code=1008)
        return

    session = _make_session()
    try:
        await session.start(url or "about:blank", headless=_HEADLESS)

        async def _on_frame(data: str) -> None:
            try:
                await websocket.send_json({"kind": "frame", "data": data})
            except Exception:  # noqa: BLE001 — client gone; stream ends in the loop
                pass

        await session.start_screencast(_on_frame)

        while True:
            msg = await websocket.receive_json()
            response = await handle_client_message(session, msg)
            if response is not None:
                await websocket.send_json(response)
    except WebSocketDisconnect:
        pass
    finally:
        await session.stop()
