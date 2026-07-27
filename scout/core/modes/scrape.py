"""Scrape mode — single URL fetch to clean markdown + optional screenshot.

Returns ScrapeResponse with:
- markdown: clean filtered content (primary, always populated on success)
- raw_html: original HTML (only if ScoutFormats.RAW_HTML in formats)
- screenshot_base64: PNG base64 (only if ScoutFormats.SCREENSHOT in formats)
- links: all internal and external hrefs extracted from page
- metadata: title, description, word_count, token_estimate, language
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
import hashlib
from typing import cast
from urllib.parse import urlparse

import structlog
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, CrawlResult
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from scout.core.pdf import extract_pdf_text, fetch_pdf_bytes, looks_like_pdf_url
from scout.core.types import ScoutFormats, ScoutMetadata, ScrapeRequest, ScrapeResponse

logger = structlog.get_logger(__name__)

# FX-1a: bounded retry on transient nav/network errors only (never on
# deterministic blocks like 4xx/anti-bot responses). See
# docs/test-results-2026-07-26/FIX-PLAN.md FX-1a — one confirmed transient
# failure (net::ERR_HTTP2_PROTOCOL_ERROR under memory pressure) used to fail
# the whole run with no retry.
MAX_TRANSIENT_RETRIES = 2
RETRY_BACKOFF_SECONDS = 0.5

_TRANSIENT_ERROR_SIGNATURES = (
    "net::err_http2_protocol_error",
    "net::err_connection_reset",
    "net::err_connection_closed",
    "net::err_connection_refused",
    "net::err_connection_timed_out",
    "net::err_connection_aborted",
    "net::err_empty_response",
    "net::err_network_changed",
    "net::err_timed_out",
    "timeout",
)


def _is_transient_error(error_message: str | None, status_code: int | None) -> bool:
    """Whether a failed fetch looks like a transient blip worth retrying.

    Deterministic blocks (4xx/5xx from the server — anti-bot, not-found,
    etc.) are NOT retried; retrying those just burns time on a fetch that
    will fail the same way every time.
    """
    if status_code is not None and 400 <= status_code < 600:
        return False
    lowered = (error_message or "").lower()
    return any(signature in lowered for signature in _TRANSIENT_ERROR_SIGNATURES)


def _status_code_of(result: object) -> int | None:
    """Read status_code off a crawl4ai result, tolerating mocks/older versions."""
    value = getattr(result, "status_code", None)
    return value if isinstance(value, int) else None


def _failure_reason(result: object) -> str:
    """Build a non-empty diagnostic string for a failed crawl4ai result.

    FX-1c: the observed bug was a failed scrape returning BOTH
    status_code=None and error_message=None with no diagnostic anywhere —
    impossible to support or debug. This always returns something useful.
    """
    error_message = getattr(result, "error_message", None)
    if error_message:
        return str(error_message)
    status_code = _status_code_of(result)
    if status_code is not None:
        return f"HTTP {status_code}"
    return "Crawl failed with no error detail or status code from crawl4ai"


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
        # FX-10a: crawl4ai defaults check_robots_txt to False. Scout defaults to
        # respecting robots.txt; respect_robots_txt=False on the request opts out.
        "check_robots_txt": req.respect_robots_txt,
    }
    if req.mean_delay is not None:
        kwargs["mean_delay"] = req.mean_delay
    return CrawlerRunConfig(**kwargs)


async def _scrape_pdf(req: ScrapeRequest, crawled_at: str, started: float) -> ScrapeResponse:
    """FX-11 Build 1: fetch a PDF URL and extract text via pypdf.

    Bypasses Crawl4AI/the browser entirely — a raw PDF byte stream doesn't
    need JS rendering, and Crawl4AI has no supported public API for PDF
    text extraction (see scout.core.pdf module docstring).
    """

    def _empty_meta() -> ScoutMetadata:
        return ScoutMetadata(url=req.url, crawled_at=crawled_at)

    try:
        pdf_bytes = await fetch_pdf_bytes(req.url, timeout_ms=req.timeout_ms)
        markdown, pdf_meta = extract_pdf_text(pdf_bytes)
    except Exception as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.warning("[scout/scrape] pdf extraction failed", url=req.url, error=str(exc))
        score, reasons, collector, collector_reason = _quality_score(
            title="", markdown="", links=[], success=False, error=str(exc)
        )
        return ScrapeResponse(
            success=False,
            url=req.url,
            metadata=_empty_meta(),
            fetched_at=crawled_at,
            provider="pdf",
            quality_score=score,
            quality_reasons=reasons,
            recommended_collector=collector,
            recommended_collector_reason=collector_reason,
            error=str(exc),
            duration_ms=duration_ms,
        )

    duration_ms = int((time.monotonic() - started) * 1000)
    metadata = ScoutMetadata(
        url=req.url,
        crawled_at=crawled_at,
        title=pdf_meta.title,
        word_count=_count_words(markdown),
        token_estimate=_estimate_tokens(markdown),
    )
    quality, quality_reasons, collector, collector_reason = _quality_score(
        title=pdf_meta.title, markdown=markdown, links=[], success=True
    )
    return ScrapeResponse(
        success=True,
        url=req.url,
        status_code=200,
        markdown=markdown,
        raw_markdown=markdown,
        clean_markdown=markdown,
        metadata=metadata,
        final_url=req.url,
        fetched_at=crawled_at,
        provider="pdf",
        content_hash=_content_hash(markdown),
        cleanup_rules_applied=["pypdf.extract_text"],
        quality_score=quality,
        quality_reasons=quality_reasons,
        recommended_collector=collector,
        recommended_collector_reason=collector_reason,
        duration_ms=duration_ms,
        pdf=pdf_meta,
    )


async def scrape(req: ScrapeRequest) -> ScrapeResponse:
    """Fetch a single URL and return clean content."""
    started = time.monotonic()
    crawled_at = datetime.now(timezone.utc).isoformat()

    if looks_like_pdf_url(req.url):
        return await _scrape_pdf(req, crawled_at, started)

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
        # FX-4: each attempt gets its OWN `async with AsyncWebCrawler(...)`
        # block — i.e. a fresh browser context — rather than retrying
        # `arun()` on the same crawler that just failed. Under sustained
        # load a net::ERR_HTTP2_PROTOCOL_ERROR can leave that context's
        # underlying connection/browser state poisoned, so reusing it just
        # reproduces the same failure. Bounded by MAX_TRANSIENT_RETRIES.
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            # arun() returns CrawlResultContainer whose __getattr__ delegates to _results[0].
            # Cast to CrawlResult so pyright can resolve attributes; runtime behaviour is unchanged.
            result = cast(CrawlResult, await crawler.arun(req.url, config=run_cfg))

        attempt = 1
        while not result.success and attempt <= MAX_TRANSIENT_RETRIES:
            error_message = getattr(result, "error_message", None)
            status_code = _status_code_of(result)
            if not _is_transient_error(error_message, status_code):
                break
            logger.warning(
                "[scout/scrape] transient error, retrying with fresh browser context",
                url=req.url,
                attempt=attempt,
                max_retries=MAX_TRANSIENT_RETRIES,
                error=error_message,
                status_code=status_code,
            )
            await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)
            async with AsyncWebCrawler(config=browser_cfg) as retry_crawler:
                result = cast(CrawlResult, await retry_crawler.arun(req.url, config=run_cfg))
            attempt += 1

        duration_ms = int((time.monotonic() - started) * 1000)

        if not result.success:
            status_code = _status_code_of(result)
            error_reason = _failure_reason(result)
            logger.warning(
                "[scout/scrape] crawl failed",
                url=req.url,
                status_code=status_code,
                error=error_reason,
            )
            score, reasons, collector, collector_reason = _quality_score(
                title="",
                markdown="",
                links=[],
                success=False,
                error=error_reason,
            )
            return ScrapeResponse(
                success=False,
                url=req.url,
                status_code=status_code,
                metadata=_empty_meta(),
                fetched_at=crawled_at,
                provider="crawl4ai",
                quality_score=score,
                quality_reasons=reasons,
                recommended_collector=collector,
                recommended_collector_reason=collector_reason,
                error=error_reason,
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
            status_code=_status_code_of(result),
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
