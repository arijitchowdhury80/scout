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
