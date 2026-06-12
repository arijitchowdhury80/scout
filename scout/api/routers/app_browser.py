"""User Browser CDP endpoints for the Scout app."""

from __future__ import annotations

from fastapi import APIRouter

from scout.api.user_browser import (
    UserBrowserCaptureRequest,
    UserBrowserOpenRequest,
    UserBrowserSessionState,
    browser_service,
)

router = APIRouter(prefix="/app/browser", tags=["app-browser"])


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
