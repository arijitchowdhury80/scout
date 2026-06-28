"""Scrape mode — single URL fetch to clean markdown + optional screenshot.

Returns ScrapeResponse with:
- markdown: clean filtered content (primary, always populated on success)
- raw_html: original HTML (only if ScoutFormats.RAW_HTML in formats)
- screenshot_base64: PNG base64 (only if ScoutFormats.SCREENSHOT in formats)
- links: all internal and external hrefs extracted from page
- metadata: title, description, word_count, token_estimate, language
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
import hashlib
from typing import cast
from urllib.parse import urlparse

import structlog
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, CrawlResult
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from scout.core.types import ScoutFormats, ScoutMetadata, ScrapeRequest, ScrapeResponse

logger = structlog.get_logger(__name__)


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~0.75 tokens per word (4 chars avg)."""
    return max(1, len(text) // 4)


def _count_words(text: str) -> int:
    """Return number of whitespace-separated words in text."""
    return len(text.split())


def _extract_links(links_dict: dict) -> list[str]:
    """Flatten crawl4ai links dict to a list of hrefs."""
    result = []
    for link in links_dict.get("internal", []):
        href = link.get("href", "")
        if href:
            result.append(href)
    for link in links_dict.get("external", []):
        href = link.get("href", "")
        if href:
            result.append(href)
    return result


def _content_hash(*parts: str) -> str:
    content = "\n".join(part for part in parts if part)
    return hashlib.sha256(content.encode("utf-8")).hexdigest() if content else ""


def _quality_score(
    *,
    title: str,
    markdown: str,
    links: list[str],
    success: bool,
    error: str = "",
) -> tuple[float, list[str], str, str]:
    reasons: list[str] = []
    score = 0.0
    if success:
        score += 0.25
        reasons.append("not_blocked")
    elif error:
        reasons.append("fetch_failed")
    if title:
        score += 0.2
        reasons.append("title_present")
    if len(markdown.split()) >= 20:
        score += 0.25
        reasons.append("content_present")
    else:
        reasons.append("content_sparse")
    if links:
        score += 0.15
        reasons.append("links_extracted")
    if markdown and not _looks_like_blocked(markdown):
        score += 0.15
        reasons.append("not_blocked_copy")
    elif markdown:
        reasons.append("blocked_copy_detected")
    score = round(min(score, 1.0), 2)
    collector = "crawl4ai" if score >= 0.55 else "direct_http_or_feed"
    collector_reason = (
        "Crawl4AI returned usable rendered content."
        if collector == "crawl4ai"
        else "Rendered content was sparse or blocked; consider direct HTTP, RSS/feed, or browser capture."
    )
    return score, reasons, collector, collector_reason


def _looks_like_blocked(markdown: str) -> bool:
    lowered = markdown.lower()
    return any(
        marker in lowered
        for marker in [
            "access denied",
            "captcha",
            "checking your browser",
            "verify you are human",
            "blocked",
        ]
    )


def _build_browser_config(req: ScrapeRequest) -> BrowserConfig:
    """Map a ScrapeRequest onto Crawl4AI BrowserConfig (read receipt 2026-06-17:
    proxy / user_agent / user_agent_mode are BrowserConfig params)."""
    kwargs: dict = {
        "headless": req.headless,
        "java_script_enabled": req.use_js,
        "enable_stealth": req.stealth,
    }
    if req.proxy:
        # 'proxy' is deprecated in Crawl4AI; use proxy_config (Playwright shape).
        parsed = urlparse(req.proxy)
        server = parsed.scheme + "://" + (parsed.hostname or "")
        if parsed.port:
            server += f":{parsed.port}"
        proxy_config: dict = {"server": server}
        if parsed.username:
            proxy_config["username"] = parsed.username
        if parsed.password:
            proxy_config["password"] = parsed.password
        kwargs["proxy_config"] = proxy_config
    if req.user_agent:
        kwargs["user_agent"] = req.user_agent
    if req.user_agent_mode:
        kwargs["user_agent_mode"] = req.user_agent_mode
    return BrowserConfig(**kwargs)


def _build_run_config(req: ScrapeRequest, *, want_screenshot: bool) -> CrawlerRunConfig:
    """Map a ScrapeRequest onto Crawl4AI CrawlerRunConfig (read receipt:
    simulate_user / magic / override_navigator / mean_delay live here)."""
    kwargs: dict = {
        "cache_mode": CacheMode.BYPASS,
        "screenshot": want_screenshot,
        "page_timeout": req.timeout_ms,
        "wait_for": req.wait_for,
        "simulate_user": req.stealth,
        "magic": req.stealth,
        # stealth runs get navigator override for free; or opt in explicitly
        "override_navigator": req.stealth or req.override_navigator,
    }
    if req.mean_delay is not None:
        kwargs["mean_delay"] = req.mean_delay
    return CrawlerRunConfig(**kwargs)


async def scrape(req: ScrapeRequest) -> ScrapeResponse:
    """Fetch a single URL and return clean content."""
    started = time.monotonic()
    crawled_at = datetime.now(timezone.utc).isoformat()

    want_screenshot = ScoutFormats.SCREENSHOT in req.formats
    want_raw_html = ScoutFormats.RAW_HTML in req.formats

    md_generator = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.4, threshold_type="fixed")
    )
    browser_cfg = _build_browser_config(req)
    run_cfg = _build_run_config(req, want_screenshot=want_screenshot)
    run_cfg.markdown_generator = md_generator

    def _empty_meta() -> ScoutMetadata:
        return ScoutMetadata(url=req.url, crawled_at=crawled_at)

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            # arun() returns CrawlResultContainer whose __getattr__ delegates to _results[0].
            # Cast to CrawlResult so pyright can resolve attributes; runtime behaviour is unchanged.
            result = cast(CrawlResult, await crawler.arun(req.url, config=run_cfg))

        duration_ms = int((time.monotonic() - started) * 1000)

        if not result.success:
            logger.warning("[scout/scrape] crawl failed", url=req.url, error=result.error_message)
            score, reasons, collector, collector_reason = _quality_score(
                title="",
                markdown="",
                links=[],
                success=False,
                error=result.error_message or "Unknown error",
            )
            return ScrapeResponse(
                success=False,
                url=req.url,
                metadata=_empty_meta(),
                fetched_at=crawled_at,
                provider="crawl4ai",
                quality_score=score,
                quality_reasons=reasons,
                recommended_collector=collector,
                recommended_collector_reason=collector_reason,
                error=result.error_message or "Unknown error",
                duration_ms=duration_ms,
            )

        # result.markdown is StringCompatibleMarkdown (has .fit_markdown via __getattr__) or None.
        # Use getattr so tests that pass plain strings as markdown mock values don't break.
        _md = result.markdown
        clean_md = getattr(_md, "fit_markdown", None) or str(_md or "") or ""
        raw_md = str(_md or "")
        raw_meta = result.metadata or {}
        links = _extract_links(result.links or {})
        final_url = result.url or req.url
        raw_html = (result.html or "") if want_raw_html else ""
        screenshot = (result.screenshot or "") if want_screenshot else ""
        quality, quality_reasons, collector, collector_reason = _quality_score(
            title=raw_meta.get("title", "") or "",
            markdown=clean_md,
            links=links,
            success=True,
        )

        metadata = ScoutMetadata(
            url=final_url,
            crawled_at=crawled_at,
            title=raw_meta.get("title", "") or "",
            description=raw_meta.get("description", "") or "",
            language=raw_meta.get("language", "") or "",
            word_count=_count_words(clean_md),
            token_estimate=_estimate_tokens(clean_md),
        )

        return ScrapeResponse(
            success=True,
            url=final_url,
            markdown=clean_md,
            raw_markdown=raw_md,
            clean_markdown=clean_md,
            raw_html=raw_html,
            screenshot_base64=screenshot,
            links=links,
            metadata=metadata,
            final_url=final_url,
            fetched_at=crawled_at,
            provider="crawl4ai",
            content_hash=_content_hash(raw_md, clean_md, raw_html),
            cleanup_rules_applied=["PruningContentFilter(threshold=0.4,fixed)"],
            quality_score=quality,
            quality_reasons=quality_reasons,
            recommended_collector=collector,
            recommended_collector_reason=collector_reason,
            duration_ms=duration_ms,
        )

    except Exception as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.exception("[scout/scrape] unexpected error", url=req.url, exc=str(exc))
        score, reasons, collector, collector_reason = _quality_score(
            title="",
            markdown="",
            links=[],
            success=False,
            error=str(exc),
        )
        return ScrapeResponse(
            success=False,
            url=req.url,
            metadata=_empty_meta(),
            fetched_at=crawled_at,
            provider="crawl4ai",
            quality_score=score,
            quality_reasons=reasons,
            recommended_collector=collector,
            recommended_collector_reason=collector_reason,
            error=str(exc),
            duration_ms=duration_ms,
        )
