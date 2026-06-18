"""Live browser session — the engine behind Scout's EMBEDDED browser pane.

Streams a real Chromium's frames out (CDP Page.startScreencast) and forwards the
human's clicks/keys from the Scout UI back in (CDP Input.*). This is what makes
the browser live *inside* the Scout UI instead of in a separate window, and it
is consumed by both front doors (the web UI's canvas pane and the HTTP/WS API
that other apps embed).

`input_event_to_cdp` is the pure, fully-tested mapping from UI canvas events to
CDP commands. The session class wraps Playwright's CDP session for the live
plumbing (screencast frames + input dispatch + snapshot for block detection).

KNOWN OPEN QUESTION (to validate live): CDP-forwarded input may not clear
behavioral challenges (PerimeterX press-and-hold) the way native OS input does —
the same signal that re-challenged crawl-from-here. If embedded-solve fails a
given wall, the ladder falls back to a native browser window for that solve.
"""

from __future__ import annotations

from typing import Any

# Map a UI mouse "button" string to the CDP button name.
_BUTTONS = {"left", "middle", "right", "back", "forward"}


def input_event_to_cdp(event: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Translate a Scout-UI canvas input event into a (CDP method, params) pair.

    Raises ValueError on an unrecognized event type so the relay never silently
    drops a human's interaction.
    """
    etype = event.get("type", "")

    if etype in ("mousemove", "mousedown", "mouseup"):
        cdp_type = {
            "mousemove": "mouseMoved",
            "mousedown": "mousePressed",
            "mouseup": "mouseReleased",
        }[etype]
        button = event.get("button", "left")
        if button not in _BUTTONS:
            button = "left"
        params: dict[str, Any] = {
            "type": cdp_type,
            "x": event.get("x", 0),
            "y": event.get("y", 0),
            "button": button,
        }
        if etype != "mousemove":
            params["clickCount"] = event.get("clickCount", 1)
        return "Input.dispatchMouseEvent", params

    if etype == "wheel":
        return "Input.dispatchMouseEvent", {
            "type": "mouseWheel",
            "x": event.get("x", 0),
            "y": event.get("y", 0),
            "deltaX": event.get("deltaX", 0),
            "deltaY": event.get("deltaY", 0),
        }

    if etype in ("keydown", "keyup"):
        cdp_type = "keyDown" if etype == "keydown" else "keyUp"
        params = {"type": cdp_type, "key": event.get("key", "")}
        if "text" in event:
            params["text"] = event["text"]
        return "Input.dispatchKeyEvent", params

    raise ValueError(f"Unknown input event type: {etype!r}")


class LiveBrowserSession:
    """A live, controllable Chromium session for the embedded pane.

    Lazily imports Playwright so importing this module stays cheap and the engine
    has no hard import-time browser dependency.
    """

    def __init__(self) -> None:
        self._pw: Any = None
        self._browser: Any = None
        self._page: Any = None
        self._cdp: Any = None

    async def start(self, url: str, *, headless: bool = False) -> None:
        from playwright.async_api import async_playwright

        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=headless)
        self._page = await self._browser.new_page()
        self._cdp = await self._page.context.new_cdp_session(self._page)
        await self._page.goto(url, wait_until="domcontentloaded")

    async def start_screencast(
        self, on_frame: Any, *, quality: int = 60, max_width: int = 1280, max_height: int = 800
    ) -> None:
        """Begin streaming JPEG frames; `on_frame(data_b64)` is called per frame."""

        async def _handler(params: dict[str, Any]) -> None:
            await on_frame(params.get("data", ""))
            try:
                await self._cdp.send(
                    "Page.screencastFrameAck", {"sessionId": params["sessionId"]}
                )
            except Exception:  # noqa: BLE001 — a dropped ack must not kill the stream
                pass

        self._cdp.on("Page.screencastFrame", lambda p: _ensure_task(_handler(p)))
        await self._cdp.send(
            "Page.startScreencast",
            {"format": "jpeg", "quality": quality, "maxWidth": max_width, "maxHeight": max_height},
        )

    async def dispatch(self, event: dict[str, Any]) -> None:
        """Forward one UI input event into the live page via CDP."""
        method, params = input_event_to_cdp(event)
        await self._cdp.send(method, params)

    async def snapshot(self) -> tuple[str, str, str]:
        """Return (url, title, html) of the live page for block detection / harvest."""
        title = await self._page.title()
        html = await self._page.content()
        return self._page.url, title, html

    async def stop(self) -> None:
        for closer in (
            lambda: self._cdp and self._cdp.detach(),
            lambda: self._browser and self._browser.close(),
            lambda: self._pw and self._pw.stop(),
        ):
            try:
                result = closer()
                if result is not None:
                    await result
            except Exception:  # noqa: BLE001 — best-effort teardown
                pass


def _ensure_task(coro: Any) -> None:
    import asyncio

    asyncio.ensure_future(coro)
