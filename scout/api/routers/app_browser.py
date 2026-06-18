"""User Browser CDP endpoints for the Scout app."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from scout.api.user_browser import (
    UserBrowserCaptureRequest,
    UserBrowserOpenRequest,
    UserBrowserSessionState,
    browser_service,
)
from scout.core.blocking import detect_block

router = APIRouter(prefix="/app/browser", tags=["app-browser"])


class NativeCaptureResult(BaseModel):
    """Result of capturing the Scout-managed native Chrome's active tab, with a
    block verdict so the UI knows whether the human still needs to solve."""

    url: str = ""
    title: str = ""
    chars: int = 0
    blocked: bool = False
    vendor: str = ""
    text: str = ""
    error: str = ""


@router.post("/capture", response_model=NativeCaptureResult)
async def capture_native(req: UserBrowserOpenRequest) -> NativeCaptureResult:
    """Capture the native browser's current page; report if it's still blocked.

    The native-window fallback for behavioral walls the embedded canvas can't
    clear (forwarded press-and-hold fails PerimeterX — live finding 2026-06-18).
    """
    try:
        cap = await browser_service.capture_active_tab(req.url)
    except Exception as exc:  # noqa: BLE001 — no session / unreachable: tell the UI
        return NativeCaptureResult(error=str(exc))
    signal = detect_block(None, title=cap.title, html=cap.html, markdown=cap.text)
    return NativeCaptureResult(
        url=cap.url,
        title=cap.title,
        chars=len(cap.html),
        blocked=signal.blocked,
        vendor=signal.vendor,
        text=cap.text[:2_000_000],  # full clean text of the cleared page
    )


@router.post("/open", response_model=UserBrowserSessionState)
async def open_user_browser(req: UserBrowserOpenRequest) -> UserBrowserSessionState:
    return await browser_service.open_browser(req)


@router.get("/status", response_model=UserBrowserSessionState)
async def get_user_browser_status() -> UserBrowserSessionState:
    return await browser_service.status()


__all__ = [
    "UserBrowserCaptureRequest",
    "UserBrowserOpenRequest",
    "UserBrowserSessionState",
    "browser_service",
    "router",
]
