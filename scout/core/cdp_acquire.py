"""Crawl4AI-over-CDP acquisition — attach the core engine to an already-open
browser tab and structure it WITHOUT navigating.

This is how Scout keeps Crawl4AI as THE engine even on the hardest path. The
automated browser cannot clear behavioral walls (PerimeterX/DataDome), so a
human clears the wall once in real Chrome. We then point Crawl4AI at that same
running Chrome over CDP and let it drive the cleared tab — fetch (read the live
DOM) and extract (markdown + records) both run through the core, not raw
Playwright.

The cleared tab is NEVER re-navigated: `CrawlerRunConfig(js_only=True)` skips
`page.goto` (async_crawler_strategy.py:666-681), so the wall the human just
solved is not re-triggered. Crawl4AI's managed-browser `get_page` adopts the
existing tab whose URL matches (browser_manager.py:1078), so we drive the exact
page the human cleared — and `scan_full_page` scrolls it to flush lazy-loaded
content before extraction (fixes the "Loading…" snapshot gaps).

Falls back nowhere: on any failure it degrades honestly to success=False. The
caller (native capture) keeps the static raw:// snapshot as its fallback.
"""

from __future__ import annotations

import time
from typing import cast

import structlog
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    CrawlResult,
    JsonCssExtractionStrategy,
    LLMConfig,
    LLMExtractionStrategy,
)
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from scout.core.capture_extract import _coerce_records
from scout.core.types import CaptureExtraction

logger = structlog.get_logger(__name__)


async def acquire_open_page(
    cdp_url: str,
    url: str,
    *,
    css_schema: dict | None = None,
    llm_schema: dict | None = None,
    instruction: str = "",
    llm_api_key: str = "",
    llm_provider: str = "gemini/gemini-2.0-flash",
    scan_full_page: bool = True,
) -> CaptureExtraction:
    """Attach Crawl4AI to a running Chrome over CDP and structure the current
    (human-cleared) tab without navigating.

    Args:
        cdp_url: CDP endpoint of the already-open Chrome, e.g.
            "http://127.0.0.1:49321" (the debugging port the human-solve window
            launched with).
        url: the URL of the cleared tab — used so Crawl4AI's get_page adopts the
            exact existing tab (matched by url) rather than a blank one.
        scan_full_page: auto-scroll the tab to flush lazy-loaded content first.

    Returns a CaptureExtraction; degrades honestly to success=False on failure.
    """
    started = time.monotonic()

    if not cdp_url:
        return CaptureExtraction(
            success=False,
            source_url=url,
            error="No CDP endpoint to attach to.",
            duration_ms=int((time.monotonic() - started) * 1000),
        )

    extraction_strategy = None
    if llm_schema and llm_api_key:
        extraction_strategy = LLMExtractionStrategy(
            llm_config=LLMConfig(provider=llm_provider, api_token=llm_api_key),
            schema=llm_schema,
            extraction_type="schema",
            instruction=instruction,
            extra_args={"temperature": 0, "max_tokens": 2000},
        )
    elif css_schema:
        extraction_strategy = JsonCssExtractionStrategy(schema=css_schema)

    md_generator = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.4, threshold_type="fixed")
    )
    # browser_mode="cdp" → connect_over_cdp to the human-cleared Chrome.
    browser_cfg = BrowserConfig(browser_mode="cdp", cdp_url=cdp_url, headless=False)
    # js_only=True → process the CURRENT tab; do NOT goto (no wall re-trigger).
    run_cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, js_only=True)
    run_cfg.markdown_generator = md_generator
    run_cfg.scan_full_page = scan_full_page
    if extraction_strategy is not None:
        run_cfg.extraction_strategy = extraction_strategy

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = cast(CrawlResult, await crawler.arun(url, config=run_cfg))

        duration_ms = int((time.monotonic() - started) * 1000)

        if not result.success:
            return CaptureExtraction(
                success=False,
                source_url=url,
                error=result.error_message or "CDP acquisition failed.",
                duration_ms=duration_ms,
            )

        _md = result.markdown
        clean_md = getattr(_md, "fit_markdown", None) or str(_md or "") or ""
        records = _coerce_records(result.extracted_content)

        return CaptureExtraction(
            success=True,
            source_url=result.url or url,
            markdown=clean_md,
            records=records,
            record_count=len(records),
            word_count=len(clean_md.split()),
            duration_ms=duration_ms,
        )

    except Exception as exc:  # noqa: BLE001 — degrade honestly, never fake records
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.exception("[scout/cdp-acquire] error", source_url=url, exc=str(exc))
        return CaptureExtraction(
            success=False,
            source_url=url,
            error=str(exc),
            duration_ms=duration_ms,
        )


__all__ = ["acquire_open_page"]
