"""Map mode — fast URL discovery without content extraction.

Uses BFS prefetch mode to discover all URLs on a site without
processing page content. ~200-500ms per page instead of 2-5s.
Use this before /crawl to understand site structure.
"""
from __future__ import annotations

import time

import structlog
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai import BFSDeepCrawlStrategy, FilterChain, URLPatternFilter

from scout.core.types import MapRequest, MapResponse

logger = structlog.get_logger(__name__)


async def map_urls(req: MapRequest) -> MapResponse:
    """Discover all URLs on a site. No content extraction."""
    started = time.monotonic()

    filters = []
    if req.url_pattern:
        filters.append(URLPatternFilter(patterns=[req.url_pattern]))

    strategy = BFSDeepCrawlStrategy(
        max_depth=3,
        max_pages=req.max_pages,
        include_external=req.include_external,
        filter_chain=FilterChain(filters) if filters else None,
    )

    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        deep_crawl_strategy=strategy,
        word_count_threshold=1,
    )
    browser_cfg = BrowserConfig(headless=True, java_script_enabled=False)

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            discovered: list[str] = []
            async for result in await crawler.arun_many([req.url], config=run_cfg):
                if result.url:
                    discovered.append(result.url)

        duration_ms = int((time.monotonic() - started) * 1000)
        logger.info("[scout/map] complete", start_url=req.url, urls=len(discovered))
        return MapResponse(success=True, start_url=req.url, urls=discovered, total=len(discovered), duration_ms=duration_ms)

    except Exception as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.exception("[scout/map] error", url=req.url, exc=str(exc))
        return MapResponse(success=False, start_url=req.url, urls=[], total=0, error=str(exc), duration_ms=duration_ms)
