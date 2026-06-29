"""Static launch website helpers for serving the product site from Scout API."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


router = APIRouter(include_in_schema=False)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WEBSITE_DIR = _REPO_ROOT / "website"


@router.get("/")
async def launch_site_index() -> FileResponse:
    """Serve the Scout marketing website as the public root."""
    return FileResponse(_WEBSITE_DIR / "index.html", media_type="text/html")


@router.get("/styles.css")
async def launch_site_styles() -> FileResponse:
    """Serve launch-site CSS from the API origin."""
    return FileResponse(_WEBSITE_DIR / "styles.css", media_type="text/css")


@router.get("/assets/warm-industrial-design-system/{asset_name}")
async def launch_site_design_system_asset(asset_name: str) -> FileResponse:
    """Serve the bundled launch-site design-system assets."""
    allowed_assets = {"warm-industrial.css", "README.md", "index.html"}
    if asset_name not in allowed_assets:
        raise HTTPException(status_code=404, detail="Launch site asset not found.")
    return FileResponse(
        _WEBSITE_DIR / "assets" / "warm-industrial-design-system" / asset_name,
        media_type=_asset_media_type(asset_name),
    )


def _asset_media_type(asset_name: str) -> str:
    """Return a conservative media type for static launch assets."""
    if asset_name.endswith(".css"):
        return "text/css"
    if asset_name.endswith(".html"):
        return "text/html"
    return "text/plain"


@router.get("/quickstart")
@router.get("/quickstart.html")
async def launch_site_quickstart() -> FileResponse:
    """Serve the Scout local-install quickstart page."""
    return _launch_site_page("quickstart.html")


@router.get("/pricing")
@router.get("/pricing.html")
async def launch_site_pricing() -> FileResponse:
    """Serve the Scout pricing and hosted-limits page."""
    return _launch_site_page("pricing.html")


@router.get("/status")
@router.get("/status.html")
async def launch_site_status() -> FileResponse:
    """Serve the Scout launch readiness status page."""
    return _launch_site_page("status.html")


@router.get("/beta")
@router.get("/beta.html")
async def launch_site_beta() -> FileResponse:
    """Serve the Scout private-beta onboarding page."""
    return _launch_site_page("beta.html")


@router.get("/legal")
@router.get("/legal.html")
async def launch_site_legal() -> FileResponse:
    """Serve the Scout legal and third-party notices page."""
    return _launch_site_page("legal.html")


@router.get("/terms")
@router.get("/terms.html")
async def launch_site_terms() -> FileResponse:
    """Serve the Scout beta terms placeholder page."""
    return _launch_site_page("terms.html")


@router.get("/privacy")
@router.get("/privacy.html")
async def launch_site_privacy() -> FileResponse:
    """Serve the Scout beta privacy placeholder page."""
    return _launch_site_page("privacy.html")


@router.get("/third-party-notices")
@router.get("/THIRD_PARTY_NOTICES.md")
async def launch_site_third_party_notices() -> FileResponse:
    """Serve the source third-party notices file from the public website."""
    return FileResponse(_REPO_ROOT / "THIRD_PARTY_NOTICES.md", media_type="text/plain")


def _launch_site_page(page_file: str) -> FileResponse:
    """Return a known launch-site HTML file."""
    return FileResponse(_WEBSITE_DIR / page_file, media_type="text/html")
