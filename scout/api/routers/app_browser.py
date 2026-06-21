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
from scout.core.capture_extract import structure_capture

router = APIRouter(prefix="/app/browser", tags=["app-browser"])


class NativeCaptureRequest(BaseModel):
    """Request to capture (and structure) the native Chrome's active tab.

    `css_schema` is an optional Crawl4AI JsonCss schema; when supplied, the
    cleared page is turned into typed per-item records (no LLM needed)."""

    url: str = ""
    run_id: str = ""
    profile_dir: str = ""
    css_schema: dict | None = None


class NativeCaptureResult(BaseModel):
    """Result of capturing the Scout-managed native Chrome's active tab, with a
    block verdict so the UI knows whether the human still needs to solve, plus
    the cleared page structured through Scout's Crawl4AI engine."""

    url: str = ""
    title: str = ""
    chars: int = 0
    blocked: bool = False
    vendor: str = ""
    text: str = ""
    markdown: str = ""  # clean structured markdown of the cleared page
    records: list[dict] = []  # typed records when a css_schema was supplied
    record_count: int = 0
    error: str = ""


@router.post("/capture", response_model=NativeCaptureResult)
async def capture_native(req: NativeCaptureRequest) -> NativeCaptureResult:
    """Capture the native browser's current page; report if it's still blocked.

    The native-window fallback for behavioral walls the embedded canvas can't
    clear (forwarded press-and-hold fails PerimeterX — live finding 2026-06-18).

    A cleared (non-blocked) page is run through Scout's own Crawl4AI engine via
    `structure_capture` (raw:// — no re-fetch, so the wall is not re-triggered),
    yielding clean markdown + optional typed records instead of a raw blob. A
    still-blocked page is NOT structured — the UI tells the human to solve first.
    """
    try:
        cap = await browser_service.capture_active_tab(req.url)
    except Exception as exc:  # noqa: BLE001 — no session / unreachable: tell the UI
        return NativeCaptureResult(error=str(exc))
    signal = detect_block(None, title=cap.title, html=cap.html, markdown=cap.text)

    result = NativeCaptureResult(
        url=cap.url,
        title=cap.title,
        chars=len(cap.html),
        blocked=signal.blocked,
        vendor=signal.vendor,
        text=cap.text[:2_000_000],  # full clean text of the cleared page
    )

    if not signal.blocked:
        structured = await structure_capture(
            cap.html, source_url=cap.url, css_schema=req.css_schema
        )
        if structured.success:
            result = result.model_copy(
                update={
                    "markdown": structured.markdown,
                    "records": structured.records,
                    "record_count": structured.record_count,
                }
            )

    return result


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
