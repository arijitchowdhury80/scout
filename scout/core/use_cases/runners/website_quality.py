"""Website quality runner — extracts quality signals from HTML source."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from scout.core.crawler import ScoutCrawler
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
    url = req.url or (req.targets[0] if req.targets else "")
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

    record = WebsiteQualityRecord(
        objectID=f"quality_{slug}",
        url=url,
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
