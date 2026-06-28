"""Scout FastAPI application — entry point for the HTTP service."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response

from scout.api.config import settings
from scout.api.deps import get_crawler
from scout.api.middleware.auth import AuthMiddleware
from scout.api.frontend import scout_app_html
from scout.api.routers import (
    algolia,
    app_browser,
    app_runs,
    billing,
    crawl,
    extract,
    harvest,
    health,
    live_browser,
    products,
    run,
    runs,
    structure,
    workdir,
    hosted,
)
from scout.api.routers import map as map_router
from scout.api.routers import scrape, screenshot
from scout.core.crawler import ScoutCrawler

# Re-export get_crawler so tests can import it from scout.api.main for
# dependency_overrides.
__all__ = ["app", "get_crawler"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise shared resources on startup; release them on shutdown."""
    from pathlib import Path

    from scout.api.db import RunDB
    from scout.api.run_store import bind_db
    from scout.core.platform.account_service import HostedAccountService
    from scout.core.platform.account_sqlite_store import SQLiteHostedAccountStore
    from scout.core.platform.payment_provisioning import (
        HostedPaymentProvisioningService,
        SQLiteHostedPaymentStore,
    )

    app.state.crawler = ScoutCrawler(llm_api_key=settings.llm_api_key)
    db_path = settings.resolve_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    run_db = RunDB(db_path)
    await run_db.init_db()
    app.state.run_db = run_db
    hosted_db_path = settings.resolve_hosted_account_db_path()
    Path(hosted_db_path).parent.mkdir(parents=True, exist_ok=True)
    hosted_account_service = HostedAccountService(SQLiteHostedAccountStore(hosted_db_path))
    app.state.hosted_account_service = hosted_account_service
    app.state.hosted_payment_service = HostedPaymentProvisioningService(
        hosted_account_service,
        SQLiteHostedPaymentStore(hosted_db_path),
    )
    bind_db(run_db)
    yield
    await run_db.close()


app = FastAPI(title="Scout", lifespan=lifespan)

app.add_middleware(AuthMiddleware, api_key=settings.scout_api_key)

app.include_router(health.router)
app.include_router(scrape.router)
app.include_router(crawl.router)
app.include_router(extract.router)
app.include_router(structure.router)
app.include_router(harvest.router)
app.include_router(products.router)
app.include_router(run.router)
app.include_router(runs.router)
app.include_router(algolia.router)
app.include_router(app_browser.router)
app.include_router(app_runs.router)
app.include_router(live_browser.router)
app.include_router(map_router.router)
app.include_router(screenshot.router)
app.include_router(workdir.router)
app.include_router(hosted.router)
app.include_router(billing.router)


@app.get("/api/config", include_in_schema=False)
async def api_config() -> dict[str, str]:
    """Return non-secret config the frontend needs (the API key is already known to the browser)."""
    return {"api_key": settings.scout_api_key}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root() -> str:
    """Return a tiny human-friendly landing page for browser visits."""
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <title>Scout</title>
        <style>
          body { font-family: system-ui, sans-serif; margin: 3rem; max-width: 760px; }
          code { background: #f3f4f6; padding: 0.1rem 0.3rem; border-radius: 4px; }
          a { color: #0f766e; }
        </style>
      </head>
      <body>
        <h1>Scout</h1>
        <p>Self-hosted web scraping and product intelligence built on Crawl4AI.</p>
        <ul>
          <li><a href="/health">Health</a></li>
          <li><a href="/app">Scout app</a></li>
          <li><a href="/docs">API docs</a></li>
        </ul>
        <p>CLI: <code>scout products "men shirts" --site example.com</code></p>
      </body>
    </html>
    """


@app.get("/app", response_class=HTMLResponse, include_in_schema=False)
async def scout_app() -> str:
    """Return the Scout self-educating frontend app."""
    return scout_app_html()


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    """Return an empty favicon response to keep browser probes quiet."""
    return Response(status_code=204)
