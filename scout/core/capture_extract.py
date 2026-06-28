"""Capture structuring — turn an already-fetched page into clean markdown +
optional typed records, WITHOUT re-fetching.

The native-grab fallback (human solves a behavioral wall in a real Chrome
window) captures the cleared page's HTML, but historically returned it as a
raw ~1.2M-char text blob. This module reconnects that path to Scout's own
Crawl4AI engine: the captured HTML is fed back through `AsyncWebCrawler` via
the `raw://` scheme (crawl4ai async_crawler_strategy.py:485 — strips the 6-char
prefix and processes the remainder as page HTML, status 200, no network call).

Re-fetching the live URL would re-trigger the wall the human just solved, so we
NEVER touch the network here — only structure the bytes we already hold.

Default (no schema) → clean markdown via DefaultMarkdownGenerator. When a
caller supplies a CSS schema (JsonCssExtractionStrategy, no LLM) or an LLM
schema (LLMExtractionStrategy), typed per-item records are returned too. Scout
acquires + extracts; it never interprets.
"""

from __future__ import annotations

import json
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

from scout.core.types import CaptureExtraction

logger = structlog.get_logger(__name__)


def _coerce_records(extracted_content: str | None) -> list[dict]:
    """Normalise crawl4ai's extracted_content JSON to a list of record dicts."""
    if not extracted_content:
        return []
    try:
        raw = json.loads(extracted_content)
    except (json.JSONDecodeError, ValueError):
        logger.warning("[scout/capture-extract] invalid JSON from extraction strategy")
        return []
    if isinstance(raw, list):
        return [r for r in raw if isinstance(r, dict)]
    if isinstance(raw, dict):
        return [raw]
    return []


async def structure_capture(
    html: str,
    *,
    source_url: str = "",
    css_schema: dict | None = None,
    llm_schema: dict | None = None,
    instruction: str = "",
    llm_api_key: str = "",
    llm_provider: str = "gemini/gemini-2.0-flash",
) -> CaptureExtraction:
    """Structure already-captured HTML into markdown + optional typed records.

    No network fetch occurs — the HTML is processed via Crawl4AI's `raw://`
    scheme, so a human-cleared page is never re-fetched (which would re-trigger
    the wall). Degrades honestly: a crawl failure returns success=False with the
    error, never fabricated records.
    """
    started = time.monotonic()

    if not html or not html.strip():
        return CaptureExtraction(
            success=False,
            source_url=source_url,
            error="Cannot structure an empty capture.",
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
    run_cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    run_cfg.markdown_generator = md_generator
    if extraction_strategy is not None:
        run_cfg.extraction_strategy = extraction_strategy
    # raw:// → process the HTML we already hold; no fetch, no wall re-trigger.
    browser_cfg = BrowserConfig(headless=True)

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            # arun() returns a CrawlResultContainer delegating to _results[0];
            # cast so pyright resolves attributes (runtime behaviour unchanged).
            result = cast(
                CrawlResult,
                await crawler.arun(f"raw://{html}", config=run_cfg),
            )

        duration_ms = int((time.monotonic() - started) * 1000)

        if not result.success:
            return CaptureExtraction(
                success=False,
                source_url=source_url,
                error=result.error_message or "Structuring the captured HTML failed.",
                duration_ms=duration_ms,
            )

        _md = result.markdown
        clean_md = getattr(_md, "fit_markdown", None) or str(_md or "") or ""
        records = _coerce_records(result.extracted_content)

        return CaptureExtraction(
            success=True,
            source_url=source_url,
            markdown=clean_md,
            raw_html=html,
            records=records,
            record_count=len(records),
            word_count=len(clean_md.split()),
            duration_ms=duration_ms,
        )

    except Exception as exc:  # noqa: BLE001 — degrade honestly, never fake records
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.exception("[scout/capture-extract] error", source_url=source_url, exc=str(exc))
        return CaptureExtraction(
            success=False,
            source_url=source_url,
            error=str(exc),
            duration_ms=duration_ms,
        )


__all__ = ["structure_capture"]
