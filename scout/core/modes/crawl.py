"""Crawl mode — recursive BFS crawl across multiple pages.

Follows internal links from start_url up to max_depth levels and
max_pages total. Returns a list of CrawlPage objects — one per
successfully crawled page. Failed pages are included with success=False.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import structlog
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai import BFSDeepCrawlStrategy, FilterChain, URLPatternFilter
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from scout.core.types import CrawlPage, CrawlRequest, CrawlResponse, ScoutMetadata

logger = structlog.get_logger(__name__)


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


async def crawl(req: CrawlRequest) -> CrawlResponse:
    """Recursively crawl a site and return all pages as CrawlPage objects."""
    started = time.monotonic()

    filters = []
    if req.url_pattern:
        filters.append(URLPatternFilter(patterns=[req.url_pattern]))

    strategy = BFSDeepCrawlStrategy(
        max_depth=req.max_depth,
        max_pages=req.max_pages,
        include_external=req.include_external,
        filter_chain=FilterChain(filters) if filters else None,
    )

    md_generator = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.4, threshold_type="fixed")
    )
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=md_generator,
        deep_crawl_strategy=strategy,
        page_timeout=req.timeout_ms,
    )
    browser_cfg = BrowserConfig(headless=True, java_script_enabled=req.use_js)

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            pages: list[CrawlPage] = []
            crawled_at = datetime.now(timezone.utc).isoformat()

            async for result in await crawler.arun_many([req.url], config=run_cfg):
                clean_md = getattr(result, "fit_markdown", None) or result.markdown or ""
                raw_meta = result.metadata or {}
                meta = ScoutMetadata(
                    url=result.url or req.url,
                    crawled_at=crawled_at,
                    title=raw_meta.get("title", "") or "",
                    description=raw_meta.get("description", "") or "",
                    language=raw_meta.get("language", "") or "",
                    word_count=len(clean_md.split()),
                    token_estimate=_estimate_tokens(clean_md),
                )
                if result.success:
                    pages.append(CrawlPage(url=result.url or req.url, markdown=clean_md, metadata=meta, success=True))
                else:
                    pages.append(CrawlPage(url=result.url or req.url, metadata=meta, success=False, error=result.error_message or ""))

        duration_ms = int((time.monotonic() - started) * 1000)
        logger.info("[scout/crawl] complete", start_url=req.url, pages=len(pages))
        return CrawlResponse(success=True, start_url=req.url, pages=pages, total_pages=len(pages), duration_ms=duration_ms)

    except Exception as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.exception("[scout/crawl] error", url=req.url, exc=str(exc))
        return CrawlResponse(success=False, start_url=req.url, pages=[], total_pages=0, error=str(exc), duration_ms=duration_ms)
