"""Human-assisted acquisition — the visible-browser rung of the ladder.

For sites that defeat automation (PerimeterX press-and-hold, DataDome, logins),
Scout opens a REAL, visible browser at the target and waits for a human to clear
the challenge. It polls the page; the moment the block detector sees it's clear
(and the page has real content), it captures and returns. This is the honest
answer to "100% unblock is impossible": a human clears it once, Scout does the
rest.

Engine-pure: depends only on `scout.core.blocking`. The concrete browser (the
macOS Chrome CDP bridge in scout.api) is injected as a `BrowserBridge`, and the
sleep is injected too — so this flow is fully unit-testable with no real browser
and no wall-clock delay.
"""

from __future__ import annotations

from typing import Awaitable, Callable, Literal, Protocol

from pydantic import BaseModel

from scout.core.blocking import detect_block

# A "cleared" page must be both non-blocked AND have real content, so an
# intermediate blank load isn't mistaken for success.
_MIN_CLEARED_CONTENT = 200


class CaptureLike(Protocol):
    """The shape this flow reads from a capture (duck-typed; no api import)."""

    url: str
    title: str
    html: str
    text: str


class BrowserBridge(Protocol):
    """Injected concrete browser (e.g. the Chrome CDP bridge)."""

    async def open(self, url: str) -> object: ...
    async def capture(self, url: str) -> CaptureLike: ...


class HumanAssistedOutcome(BaseModel):
    status: Literal["cleared", "timeout", "error"]
    polls: int = 0
    final_url: str = ""
    title: str = ""
    markdown: str = ""
    html: str = ""  # cleared-page HTML, so crawl-from-here can discover detail links
    blocked_vendor: str = ""
    error: str = ""


async def human_assisted_acquire(
    url: str,
    bridge: BrowserBridge,
    *,
    sleep: Callable[[float], Awaitable[None]],
    poll_interval: float = 2.0,
    max_wait: float = 120.0,
) -> HumanAssistedOutcome:
    """Open `url` in the injected browser and poll until a human clears it.

    Returns `cleared` with the captured page once the block detector sees it's
    clear with real content; `timeout` if the wait elapses (naming the last
    vendor seen); `error` if the bridge fails.
    """
    try:
        await bridge.open(url)
    except Exception as exc:  # noqa: BLE001 — surface, never crash the ladder
        return HumanAssistedOutcome(status="error", error=f"open failed: {exc}")

    waited = 0.0
    polls = 0
    last_vendor = ""

    while True:
        polls += 1
        try:
            cap = await bridge.capture(url)
        except Exception as exc:  # noqa: BLE001
            return HumanAssistedOutcome(
                status="error", polls=polls, error=f"capture failed: {exc}"
            )

        signal = detect_block(None, title=cap.title, html=cap.html, markdown=cap.text)
        content = cap.text or cap.html or ""
        if not signal.blocked and len(content) >= _MIN_CLEARED_CONTENT:
            return HumanAssistedOutcome(
                status="cleared",
                polls=polls,
                final_url=cap.url,
                title=cap.title,
                markdown=cap.text or "",
                html=cap.html or "",
            )
        last_vendor = signal.vendor

        if waited >= max_wait:
            return HumanAssistedOutcome(
                status="timeout", polls=polls, blocked_vendor=last_vendor
            )
        await sleep(poll_interval)
        waited += poll_interval
