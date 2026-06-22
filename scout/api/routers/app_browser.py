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
from scout.core.cdp_acquire import acquire_open_page

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
    blocked: bool = False
    vendor: str = ""
    markdown: str = ""
    records: list[dict] = []
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
        blocked=signal.blocked,
        vendor=signal.vendor,
    )

    if not signal.blocked:
        structured = None
        # Primary: drive the live cleared tab with Crawl4AI over CDP (the core
        # engine on a fully-rendered page — js_only, so no re-nav / wall
        # re-trigger). Falls back to structuring the static snapshot via raw://.
        state = await browser_service.status()
        if state.debugging_port:
            cdp = await acquire_open_page(
                f"http://127.0.0.1:{state.debugging_port}",
                cap.url,
                css_schema=req.css_schema,
            )
            if cdp.success:
                structured = cdp
        if structured is None:
            snapshot = await structure_capture(
                cap.html, source_url=cap.url, css_schema=req.css_schema
            )
            if snapshot.success:
                structured = snapshot
        if structured is not None:
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
