"""Website quality runner — extracts quality signals from HTML source."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from scout.core.crawler import ScoutCrawler
from scout.core.platform.targets import target_url_for_name
from scout.core.platform.types import Citation, RunRequest
from scout.core.types import ScrapeRequest, ScoutFormats
from scout.core.use_cases.runners.base import (
    evidence_from_scrape,
    make_citation,
)


class WebsiteQualityRecord(BaseModel):
    schema_version: str = "website_quality.v1"
    record_type: str = "website_quality"
    objectID: str
    url: str
    finding: str = ""
    has_viewport_meta: bool = False
    has_description_meta: bool = False
    has_og_tags: bool = False
    has_structured_data: bool = False
    uses_https: bool = False
    uses_semantic_html: bool = False
    has_h1: bool = False
    image_count: int = 0
    images_with_alt: int = 0
    word_count: int = 0
    link_count: int = 0
    source_url: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    citations: list[Citation] = Field(default_factory=list)


_SEMANTIC_TAGS = re.compile(
    r"<(?:header|nav|main|article|section|aside|footer|figure|figcaption)\b", re.I
)
_VIEWPORT = re.compile(r'<meta\s+[^>]*name=["\']viewport["\']', re.I)
_DESCRIPTION = re.compile(r'<meta\s+[^>]*name=["\']description["\']', re.I)
_OG_TAGS = re.compile(r'<meta\s+[^>]*property=["\']og:', re.I)
_STRUCTURED_DATA = re.compile(
    r'(?:<script[^>]*type=["\']application/ld\+json["\'])|(?:itemtype=["\']https?://schema\.org)',
    re.I,
)
_IMG_TAG = re.compile(r"<img\b[^>]*>", re.I)
_IMG_ALT = re.compile(r"<img\b[^>]*\balt=[\"'][^\"']+[\"']", re.I)
_H1_TAG = re.compile(r"<h1\b", re.I)
_LINK_TAG = re.compile(r"<a\s+[^>]*href=", re.I)


async def run_website_quality(req: RunRequest, crawler: ScoutCrawler) -> list[dict]:
    url = _resolve_quality_url(req)
    if not url:
        return []

    slug = re.sub(r"[^a-z0-9]+", "_", url.lower())[:40].strip("_")

    try:
        resp = await crawler.scrape(
            ScrapeRequest(
                url=url,
                formats=[ScoutFormats.MARKDOWN, ScoutFormats.RAW_HTML],
                use_js=True,
                stealth=True,
                timeout_ms=30000,
            )
        )
    except Exception:
        return []

    if not resp.success:
        return []

    html = resp.raw_html
    markdown = resp.markdown
    source = evidence_from_scrape(url, resp)

    has_viewport = bool(_VIEWPORT.search(html))
    has_description = bool(_DESCRIPTION.search(html))
    has_og = bool(_OG_TAGS.search(html))
    has_structured = bool(_STRUCTURED_DATA.search(html))
    uses_https = url.startswith("https://")
    uses_semantic = bool(_SEMANTIC_TAGS.search(html))
    has_h1 = bool(_H1_TAG.search(html))
    img_count = len(_IMG_TAG.findall(html))
    imgs_with_alt = len(_IMG_ALT.findall(html))
    word_count = len(markdown.split())
    link_count = len(_LINK_TAG.findall(html))

    signal_count = sum(
        [
            has_viewport,
            has_description,
            has_og,
            has_structured,
            uses_https,
            uses_semantic,
            has_h1,
        ]
    )
    confidence = min(0.9, 0.3 + signal_count * 0.08)
    finding = _finding_summary(
        has_viewport=has_viewport,
        has_description=has_description,
        has_og=has_og,
        has_structured=has_structured,
        uses_semantic=uses_semantic,
        has_h1=has_h1,
    )

    record = WebsiteQualityRecord(
        objectID=f"quality_{slug}",
        url=url,
        finding=finding,
        has_viewport_meta=has_viewport,
        has_description_meta=has_description,
        has_og_tags=has_og,
        has_structured_data=has_structured,
        uses_https=uses_https,
        uses_semantic_html=uses_semantic,
        has_h1=has_h1,
        image_count=img_count,
        images_with_alt=imgs_with_alt,
        word_count=word_count,
        link_count=link_count,
        source_url=url,
        confidence=confidence,
        citations=[make_citation(source, "url", url, f"Quality signals extracted from {url}")],
    )

    return [record.model_dump(mode="json")]


def _resolve_quality_url(req: RunRequest) -> str:
    candidates = [req.url, *req.targets, req.query]
    for candidate in candidates:
        value = candidate.strip()
        if not value:
            continue
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return value
        target_url = target_url_for_name(value)
        if target_url:
            return target_url
    return ""


def _finding_summary(
    *,
    has_viewport: bool,
    has_description: bool,
    has_og: bool,
    has_structured: bool,
    uses_semantic: bool,
    has_h1: bool,
) -> str:
    missing = []
    if not has_viewport:
        missing.append("viewport metadata")
    if not has_description:
        missing.append("description metadata")
    if not has_og:
        missing.append("Open Graph metadata")
    if not has_structured:
        missing.append("structured data")
    if not uses_semantic:
        missing.append("semantic HTML")
    if not has_h1:
        missing.append("primary H1")
    if not missing:
        return "Core website quality signals are present."
    return "Missing or weak quality signals: " + ", ".join(missing) + "."
