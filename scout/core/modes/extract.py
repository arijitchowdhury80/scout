"""Extract mode — LLM-based structured data extraction.

Caller provides a JSON Schema (from Pydantic .model_json_schema()) and a
natural language instruction. Scout crawls the URL, applies the schema via
LLMExtractionStrategy, and returns structured data matching the schema.

Always includes markdown fallback in case extracted_content is empty.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import structlog
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai import LLMExtractionStrategy, LLMConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from scout.core.types import ExtractRequest, ExtractResponse, ScoutMetadata

logger = structlog.get_logger(__name__)


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


async def extract(req: ExtractRequest, llm_api_key: str) -> ExtractResponse:
    """Crawl a URL and extract structured data matching req.extraction_schema."""
    started = time.monotonic()
    crawled_at = datetime.now(timezone.utc).isoformat()

    def _empty_meta() -> ScoutMetadata:
        return ScoutMetadata(url=req.url, crawled_at=crawled_at)

    extraction_strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(provider=req.llm_provider, api_token=llm_api_key),
        schema=req.extraction_schema,
        extraction_type="schema",
        instruction=req.instruction,
        extra_args={"temperature": 0, "max_tokens": 2000},
    )

    md_generator = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.4, threshold_type="fixed")
    )
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=md_generator,
        extraction_strategy=extraction_strategy,
        page_timeout=req.timeout_ms,
    )
    browser_cfg = BrowserConfig(headless=True, java_script_enabled=req.use_js)

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(req.url, config=run_cfg)

        duration_ms = int((time.monotonic() - started) * 1000)

        if not result.success:
            return ExtractResponse(
                success=False, url=req.url, metadata=_empty_meta(),
                error=result.error_message or "Crawl failed", duration_ms=duration_ms,
            )

        clean_md = getattr(result, "fit_markdown", None) or result.markdown or ""
        raw_meta = result.metadata or {}
        metadata = ScoutMetadata(
            url=result.url or req.url, crawled_at=crawled_at,
            title=raw_meta.get("title", "") or "",
            description=raw_meta.get("description", "") or "",
            language=raw_meta.get("language", "") or "",
            word_count=len(clean_md.split()),
            token_estimate=_estimate_tokens(clean_md),
        )

        data: dict = {}
        if result.extracted_content:
            try:
                data = json.loads(result.extracted_content)
            except (json.JSONDecodeError, ValueError):
                logger.warning("[scout/extract] invalid JSON from LLM", url=req.url)

        return ExtractResponse(
            success=True, url=result.url or req.url, data=data,
            markdown=clean_md, metadata=metadata, duration_ms=duration_ms,
        )

    except Exception as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.exception("[scout/extract] error", url=req.url, exc=str(exc))
        return ExtractResponse(
            success=False, url=req.url, metadata=_empty_meta(),
            error=str(exc), duration_ms=duration_ms,
        )
