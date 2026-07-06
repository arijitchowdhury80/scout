"""Static launch website helpers for serving the product site from Scout API."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


router = APIRouter(include_in_schema=False)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WEBSITE_DIR = _REPO_ROOT / "website"
_HTML_HEADERS = {"Cache-Control": "no-store"}
_ASSET_HEADERS = {"Cache-Control": "public, max-age=0, must-revalidate"}


@router.get("/")
async def launch_site_index() -> FileResponse:
    """Serve the Scout marketing website as the public root."""
    return _launch_site_page("index.html")


@router.get("/styles.css")
async def launch_site_styles() -> FileResponse:
    """Serve launch-site CSS from the API origin."""
    return _launch_site_asset_response(_WEBSITE_DIR / "styles.css", "styles.css")


@router.get("/assets/flux-design-system/{asset_name}")
async def launch_site_design_system_asset(asset_name: str) -> FileResponse:
    """Serve the bundled Flux launch-site design-system assets."""
    allowed_assets = {"fonts.css", "README.md", "tokens.css"}
    if asset_name not in allowed_assets:
        raise HTTPException(status_code=404, detail="Launch site asset not found.")
    return _launch_site_asset_response(
        _WEBSITE_DIR / "assets" / "flux-design-system" / asset_name,
        asset_name,
    )


@router.get("/assets/demo-samples/{asset_name}")
async def launch_site_demo_sample_asset(asset_name: str) -> FileResponse:
    """Serve the canned homepage-console sample records (company/screenshot tabs).

    These are static, hand-picked sample artifacts — never live crawl output —
    shown for endpoints the anonymous demo does not run live. See
    docs/product/plg-playground-ux.md and website/index.html's console script.
    """
    allowed_assets = {"company-sample.json", "screenshot-sample.png"}
    if asset_name not in allowed_assets:
        raise HTTPException(status_code=404, detail="Launch site asset not found.")
    return _launch_site_asset_response(
        _WEBSITE_DIR / "assets" / "demo-samples" / asset_name,
        asset_name,
    )


@router.get("/assets/{asset_name}")
async def launch_site_asset(asset_name: str) -> FileResponse:
    """Serve allowlisted launch-site media assets."""
    allowed_assets = {
        "account.js",
        "copy-code.js",
        "hosted-keygen.js",
        "playground.js",
        "pricing.js",
        "scout-mark.svg",
        "scout-product-demo.gif",
        "scout-wordmark.svg",
        "status.js",
    }
    if asset_name not in allowed_assets:
        raise HTTPException(status_code=404, detail="Launch site asset not found.")
    return _launch_site_asset_response(_WEBSITE_DIR / "assets" / asset_name, asset_name)


def _asset_media_type(asset_name: str) -> str:
    """Return a conservative media type for static launch assets."""
    if asset_name.endswith(".css"):
        return "text/css"
    if asset_name.endswith(".html"):
        return "text/html"
    if asset_name.endswith(".js"):
        return "text/javascript"
    if asset_name.endswith(".gif"):
        return "image/gif"
    if asset_name.endswith(".svg"):
        return "image/svg+xml"
    if asset_name.endswith(".json"):
        return "application/json"
    if asset_name.endswith(".png"):
        return "image/png"
    return "text/plain"


@router.get("/quickstart")
@router.get("/quickstart.html")
@router.get("/docs")
@router.get("/docs.html")
async def launch_site_quickstart() -> FileResponse:
    """Serve the consolidated Scout docs page."""
    return _launch_site_page("quickstart.html")


@router.get("/guide")
@router.get("/guide.html")
async def launch_site_guide() -> FileResponse:
    """Keep old guide links working by serving the consolidated docs page."""
    return _launch_site_page("quickstart.html")


@router.get("/pricing")
@router.get("/pricing.html")
async def launch_site_pricing() -> FileResponse:
    """Serve the Scout pricing and hosted-limits page."""
    return _launch_site_page("pricing.html")


@router.get("/account")
@router.get("/account.html")
async def launch_site_account() -> FileResponse:
    """Serve the hosted account self-service usage page."""
    return _launch_site_page("account.html")


@router.get("/app")
@router.get("/app.html")
@router.get("/app/runs")
@router.get("/app/destinations")
@router.get("/app/keys")
@router.get("/app/usage")
async def launch_site_app() -> FileResponse:
    """Serve the authed Scout app shell (playground, runs, destinations, keys, usage).

    A single-page shell: all /app/* sub-routes render the same HTML and let
    client-side JS switch panels. Auth is a hosted API key entered client-side
    (Bearer token, sessionStorage only) — see AuthMiddleware's public
    passthrough list, which mirrors the existing /account pattern.
    """
    return _launch_site_page("app.html")


@router.get("/examples")
@router.get("/examples.html")
async def launch_site_examples() -> FileResponse:
    """Keep old examples links working by serving the consolidated docs page."""
    return _launch_site_page("quickstart.html")



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
    return FileResponse(
        _WEBSITE_DIR / page_file,
        media_type="text/html",
        headers=_HTML_HEADERS,
    )


def _launch_site_asset_response(path: Path, asset_name: str) -> FileResponse:
    """Return a launch-site asset with deploy-safe cache headers."""
    return FileResponse(
        path,
        media_type=_asset_media_type(asset_name),
        headers=_ASSET_HEADERS,
    )
