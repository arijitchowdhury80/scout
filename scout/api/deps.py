"""Shared FastAPI dependencies — importable by all routers."""

from fastapi import Request

from scout.api.db import RunDB
from scout.core.crawler import ScoutCrawler


def get_crawler(request: Request) -> ScoutCrawler:
    """Return the ScoutCrawler instance stored on app.state at startup."""
    crawler: ScoutCrawler = request.app.state.crawler
    return crawler


def get_crawler_optional(request: Request) -> ScoutCrawler | None:
    """Return the crawler if available, else None (for seed-data fallback)."""
    return getattr(request.app.state, "crawler", None)


def get_run_db(request: Request) -> RunDB:
    """Return the RunDB instance stored on app.state at startup."""
    run_db: RunDB = request.app.state.run_db
    return run_db
