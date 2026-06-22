"""Shared utilities for intelligence vertical runners."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from scout.core.platform.types import (
    Citation,
    FetchProviderKind,
    FetchResult,
    SourceEvidence,
)
from scout.core.types import ScrapeRequest, ScrapeResponse


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slug(value: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return s or "unknown"


def make_citation(
    source: FetchResult,
    field: str,
    claim: str,
    snippet: str,
    confidence: float = 0.7,
) -> Citation:
    return Citation(
        source_id=source.evidence.source_id,
        source_url=source.evidence.source_url,
        field=field,
        claim=claim,
        snippet=snippet,
        confidence=confidence,
    )


def evidence_from_scrape(url: str, resp: ScrapeResponse) -> FetchResult:
    return FetchResult(
        evidence=SourceEvidence(
            provider=FetchProviderKind.CRAWL4AI,
            source_url=url,
            final_url=resp.url,
            fetched_at=now_iso(),
            confidence=0.8 if resp.success else 0.2,
        ),
        markdown=resp.markdown,
        text=resp.markdown,
        links=resp.links,
        raw={"title": resp.metadata.title if resp.metadata else ""},
    )


def scrape_request(url: str, use_js: bool = True) -> ScrapeRequest:
    return ScrapeRequest(url=url, use_js=use_js, stealth=True, timeout_ms=30000)


async def safe_scrape(crawler, url: str, use_js: bool = True) -> ScrapeResponse | None:
    """Scrape a URL, returning None on failure instead of raising."""
    try:
        resp = await crawler.scrape(scrape_request(url, use_js))
        if resp.success and resp.markdown.strip():
            return resp
    except Exception:
        pass
    return None
