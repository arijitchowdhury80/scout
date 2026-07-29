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
from scout.core.types import ScoutFormats, ScrapeRequest, ScrapeResponse


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
        html=resp.raw_html,
        text=resp.markdown,
        links=resp.links,
        raw={"title": resp.metadata.title if resp.metadata else ""},
    )


def scrape_request(
    url: str, use_js: bool = True, *, intelligence_render: bool = False
) -> ScrapeRequest:
    # FX-3: ScrapeRequest.formats defaults to [MARKDOWN] only, so
    # scrape()'s `want_raw_html` gate (scout/core/modes/scrape.py) never
    # populates resp.raw_html unless RAW_HTML is explicitly requested. Every
    # vertical runner (company/careers/investor/news/research/docs/social/
    # locations) reads `evidence_from_scrape(...).html` = `resp.raw_html` to
    # run JSON-LD Person / team-card parsers — without this, that HTML was
    # always empty against a real server, so those parsers silently never
    # ran (the algolia.com 0-executives finding).
    #
    # MOAT: `intelligence_render` opts a fetch into the full-render profile —
    # scroll to flush lazy-loaded exec/product cards, wait for client-side
    # hydration to paint, and drop images for speed. Only the intelligence
    # runners (company/products) pay this cost; everything else renders as
    # before (GATE 1 proof: this surfaced exec names the bare render missed,
    # e.g. Vercel's CEO, without regressing any site).
    kwargs: dict = {
        "url": url,
        "formats": [ScoutFormats.MARKDOWN, ScoutFormats.RAW_HTML],
        "use_js": use_js,
        "stealth": True,
        "timeout_ms": 30000,
    }
    if intelligence_render:
        kwargs["scan_full_page"] = True
        kwargs["delay_before_return_html"] = 2.5
        kwargs["block_images"] = True
        kwargs["timeout_ms"] = 45000  # scan + hydration delay needs more headroom
    return ScrapeRequest(**kwargs)


async def safe_scrape(
    crawler, url: str, use_js: bool = True, *, intelligence_render: bool = False
) -> ScrapeResponse | None:
    """Scrape a URL, returning None on failure instead of raising."""
    try:
        resp = await crawler.scrape(
            scrape_request(url, use_js, intelligence_render=intelligence_render)
        )
        if resp.success and resp.markdown.strip():
            return resp
    except Exception:
        pass
    return None
