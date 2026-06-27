"""Scrape mode — single URL fetch to clean markdown + optional screenshot."""

from __future__ import annotations

import hashlib
import re
import time
from datetime import datetime, timezone
from typing import cast
from urllib.parse import urlparse

import structlog
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig, CrawlResult
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from scout.core.types import (
    AcquisitionMetadata,
    ScoutFormats,
    ScoutMetadata,
    ScrapeRequest,
    ScrapeResponse,
)

logger = structlog.get_logger(__name__)

_BOILERPLATE_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("cookie_preferences", re.compile(r".*cookie preferences.*", re.I)),
    ("accept_all_cookies", re.compile(r".*accept all cookies.*", re.I)),
    ("privacy_preferences", re.compile(r".*privacy preferences.*", re.I)),
    ("newsletter_boilerplate", re.compile(r".*subscribe to.*newsletter.*", re.I)),
]
_BLOCKED_PATTERNS = [
    re.compile(r"access denied", re.I),
    re.compile(r"verify you are human", re.I),
    re.compile(r"captcha", re.I),
    re.compile(r"press and hold", re.I),
]


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~0.75 tokens per word (4 chars avg)."""
    return max(1, len(text) // 4)


def _count_words(text: str) -> int:
    """Return number of whitespace-separated words in text."""
    return len(text.split())


def _content_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


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


def _is_feed_like(url: str, text: str) -> bool:
    path = urlparse(url).path.lower()
    if path.endswith((".xml", ".rss", ".atom")) or "rss" in path:
        return True
    sample = (text or "").lstrip()[:200].lower()
    return sample.startswith("<rss") or sample.startswith("<?xml") or "<feed" in sample


def _remove_boilerplate(text: str) -> tuple[str, int, list[str]]:
    removed = 0
    rules: list[str] = []
    kept: list[str] = []
    for line in (text or "").splitlines():
        matched_rule = ""
        for name, pattern in _BOILERPLATE_RULES:
            if pattern.match(line.strip()):
                matched_rule = name
                break
        if matched_rule:
            removed += len(line)
            if matched_rule not in rules:
                rules.append(matched_rule)
        else:
            kept.append(line)
    return "\n".join(kept).strip(), removed, rules


def _marker_result(text: str, markers: list[str]) -> tuple[list[str], list[str], float]:
    found = [marker for marker in markers if marker.lower() in (text or "").lower()]
    missing = [marker for marker in markers if marker not in found]
    score = 1.0 if not markers else len(found) / len(markers)
    return found, missing, score


def _quality_reasons(
    *, title: str, text: str, links: list[str], blocked: bool, marker_score: float, removed: int
) -> list[str]:
    reasons: list[str] = []
    if title:
        reasons.append("title_present")
    if _count_words(text) >= 10:
        reasons.append("enough_text_extracted")
    if marker_score >= 1.0:
        reasons.append("expected_markers_found")
    if not blocked:
        reasons.append("not_blocked")
    if links:
        reasons.append("links_extracted")
    if removed < max(50, len(text) * 0.2):
        reasons.append("low_boilerplate_ratio")
    return reasons


def _quality_score(reasons: list[str], *, blocked: bool) -> float:
    if blocked:
        return 0.1
    weights = {
        "title_present": 0.15,
        "enough_text_extracted": 0.25,
        "expected_markers_found": 0.2,
        "not_blocked": 0.2,
        "links_extracted": 0.1,
        "low_boilerplate_ratio": 0.1,
    }
    return round(sum(weights.get(reason, 0.0) for reason in reasons), 2)


def _collector_recommendation(req: ScrapeRequest, text: str) -> tuple[str, str]:
    if _is_feed_like(req.url, text):
        return "rss_feed", "feed_like_url"
    if req.use_js or req.stealth:
        return "scout_scrape", "browser_rendered_page"
    return "direct_http", "simple_static_page"


def _build_browser_config(req: ScrapeRequest) -> BrowserConfig:
    """Map a ScrapeRequest onto Crawl4AI BrowserConfig."""
    kwargs: dict = {
        "headless": req.headless,
        "java_script_enabled": req.use_js,
        "enable_stealth": req.stealth,
    }
    if req.proxy:
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
    """Map a ScrapeRequest onto Crawl4AI CrawlerRunConfig."""
    native_cleanup = False
    kwargs: dict = {
        "cache_mode": CacheMode.BYPASS,
        "screenshot": want_screenshot,
        "page_timeout": req.timeout_ms,
        "wait_for": req.wait_for,
        "simulate_user": req.stealth,
        "magic": req.stealth,
        "override_navigator": req.stealth or req.override_navigator,
        "remove_consent_popups": native_cleanup,
        "remove_overlay_elements": native_cleanup,
    }
    if native_cleanup:
        kwargs["excluded_tags"] = ["nav", "footer", "aside"]
    if req.mean_delay is not None:
        kwargs["mean_delay"] = req.mean_delay
    return CrawlerRunConfig(**kwargs)


def _build_acquisition(
    req: ScrapeRequest,
    *,
    final_url: str,
    fetched_at: str,
    title: str,
    raw_markdown: str,
    clean_markdown: str,
    links: list[str],
    removed: int,
    cleanup_rules: list[str],
) -> AcquisitionMetadata | None:
    if not (req.quality_analysis or req.cleanup or req.expected_markers or req.recommend_collector):
        return None
    blocked = any(pattern.search(clean_markdown or raw_markdown) for pattern in _BLOCKED_PATTERNS)
    markers_found, markers_missing, marker_score = _marker_result(clean_markdown, req.expected_markers)
    reasons = _quality_reasons(
        title=title,
        text=clean_markdown,
        links=links,
        blocked=blocked,
        marker_score=marker_score,
        removed=removed,
    )
    collector, collector_reason = ("", "")
    if req.recommend_collector:
        collector, collector_reason = _collector_recommendation(req, raw_markdown)
    return AcquisitionMetadata(
        source_id=req.source_id,
        final_url=final_url,
        status_code=200,
        fetched_at=fetched_at,
        content_hash=_content_hash(raw_markdown),
        boilerplate_removed=removed,
        cleanup_rules_applied=cleanup_rules,
        blocked=blocked,
        markers_found=markers_found,
        markers_missing=markers_missing,
        marker_score=marker_score,
        quality_score=_quality_score(reasons, blocked=blocked),
        quality_reasons=reasons,
        recommended_collector=collector,
        recommended_collector_reason=collector_reason,
    )


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
            result = cast(CrawlResult, await crawler.arun(req.url, config=run_cfg))

        duration_ms = int((time.monotonic() - started) * 1000)

        if not result.success:
            logger.warning("[scout/scrape] crawl failed", url=req.url, error=result.error_message)
            return ScrapeResponse(
                success=False,
                url=req.url,
                metadata=_empty_meta(),
                error=result.error_message or "Unknown error",
                duration_ms=duration_ms,
            )

        markdown_obj = result.markdown
        raw_md = getattr(markdown_obj, "raw_markdown", None) or str(markdown_obj or "") or ""
        fit_md = getattr(markdown_obj, "fit_markdown", None) or raw_md
        cleaned_md, removed, cleanup_rules = _remove_boilerplate(fit_md) if req.cleanup else (fit_md, 0, [])
        raw_meta = result.metadata or {}
        links = _extract_links(result.links or {})
        final_url = result.url or req.url

        metadata = ScoutMetadata(
            url=final_url,
            crawled_at=crawled_at,
            title=raw_meta.get("title", "") or "",
            description=raw_meta.get("description", "") or "",
            language=raw_meta.get("language", "") or "",
            word_count=_count_words(cleaned_md),
            token_estimate=_estimate_tokens(cleaned_md),
        )
        acquisition = _build_acquisition(
            req,
            final_url=final_url,
            fetched_at=crawled_at,
            title=metadata.title,
            raw_markdown=raw_md,
            clean_markdown=cleaned_md,
            links=links,
            removed=removed,
            cleanup_rules=cleanup_rules,
        )

        include_profile_fields = acquisition is not None
        return ScrapeResponse(
            success=True,
            url=final_url,
            markdown=fit_md,
            raw_markdown=raw_md if include_profile_fields else "",
            clean_markdown=cleaned_md if include_profile_fields else "",
            raw_html=result.html or "" if want_raw_html else "",
            screenshot_base64=result.screenshot or "" if want_screenshot else "",
            links=links,
            metadata=metadata,
            acquisition=acquisition,
            duration_ms=duration_ms,
        )

    except Exception as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.exception("[scout/scrape] unexpected error", url=req.url, exc=str(exc))
        return ScrapeResponse(
            success=False,
            url=req.url,
            metadata=_empty_meta(),
            error=str(exc),
            duration_ms=duration_ms,
        )
