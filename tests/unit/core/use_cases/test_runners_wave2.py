"""Tests for Wave 2 intelligence runners — research, docs, social, and locations."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from scout.core.platform.types import RunRequest
from scout.core.types import (
    CrawlPage,
    CrawlResponse,
    ScoutMetadata,
    ScrapeResponse,
)


def _meta(url: str = "https://example.com") -> ScoutMetadata:
    return ScoutMetadata(url=url, crawled_at="2026-06-22T00:00:00Z")


def _scrape_ok(
    url: str, markdown: str, links: list[str] | None = None, raw_html: str = ""
) -> ScrapeResponse:
    return ScrapeResponse(
        success=True,
        url=url,
        markdown=markdown,
        raw_html=raw_html,
        links=links or [],
        metadata=_meta(url),
        duration_ms=100,
    )


def _scrape_fail(url: str) -> ScrapeResponse:
    return ScrapeResponse(
        success=False, url=url, markdown="", metadata=_meta(url), error="404", duration_ms=50
    )


def _mock_crawler(responses: dict[str, ScrapeResponse]) -> MagicMock:
    crawler = MagicMock()

    async def _scrape(req):
        for pattern, resp in responses.items():
            if pattern in req.url:
                return resp
        return _scrape_fail(req.url)

    crawler.scrape = AsyncMock(side_effect=_scrape)
    return crawler


def _req(
    use_case: str, query: str = "Acme Corp", url: str = "https://www.acme.com", **kw
) -> RunRequest:
    return RunRequest(use_case=use_case, query=query, url=url, mode="auto", **kw)


# ---------------------------------------------------------------------------
# Research runner
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_research_runner_extracts_summary() -> None:
    from scout.core.use_cases.runners.research import run_research

    crawler = _mock_crawler(
        {
            "acme.com": _scrape_ok(
                "https://www.acme.com/whitepaper",
                "# AI in Enterprise\n\nThis paper explores the impact of AI on enterprise workflows.\n"
                "We found significant productivity gains across all departments.",
            ),
        }
    )

    records = await run_research(
        _req(
            "research", query="AI enterprise", url="", targets=["https://www.acme.com/whitepaper"]
        ),
        crawler,
    )

    assert len(records) == 1
    assert records[0]["record_type"] == "research_record"
    assert "AI" in records[0]["title"] or "enterprise" in records[0]["summary"].lower()
    assert records[0]["confidence"] > 0.5


@pytest.mark.asyncio
async def test_research_runner_returns_empty_without_targets() -> None:
    from scout.core.use_cases.runners.research import run_research

    crawler = _mock_crawler({})
    records = await run_research(_req("research", url="", targets=[]), crawler)
    assert records == []


# ---------------------------------------------------------------------------
# Docs runner
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_docs_runner_crawls_and_extracts() -> None:
    from scout.core.use_cases.runners.docs import run_docs

    crawler = MagicMock()
    crawler.crawl = AsyncMock(
        return_value=CrawlResponse(
            success=True,
            start_url="https://docs.acme.com",
            pages=[
                CrawlPage(
                    url="https://docs.acme.com/getting-started",
                    markdown="# Getting Started\n\nInstall the SDK with pip install acme-sdk.",
                    metadata=_meta("https://docs.acme.com/getting-started"),
                    success=True,
                ),
                CrawlPage(
                    url="https://docs.acme.com/api-reference",
                    markdown="# API Reference\n\nThe REST API exposes endpoints for all resources.",
                    metadata=_meta("https://docs.acme.com/api-reference"),
                    success=True,
                ),
            ],
            total_pages=2,
            duration_ms=500,
        )
    )

    records = await run_docs(
        _req("docs", query="acme docs", url="https://docs.acme.com"),
        crawler,
    )

    assert len(records) == 2
    assert all(r["record_type"] == "research_record" for r in records)
    titles = {r["title"] for r in records}
    assert "Getting Started" in titles
    assert "API Reference" in titles


# ---------------------------------------------------------------------------
# Social runner
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_social_runner_finds_profiles_from_homepage() -> None:
    from scout.core.use_cases.runners.social import run_social

    crawler = _mock_crawler(
        {
            "acme.com": _scrape_ok(
                "https://www.acme.com",
                "Follow us:\n- https://www.linkedin.com/company/acme\n- https://twitter.com/acme\n",
                links=[
                    "https://www.linkedin.com/company/acme",
                    "https://twitter.com/acme",
                ],
            ),
            "linkedin.com": _scrape_ok(
                "https://www.linkedin.com/company/acme",
                "# Acme Corp\n\n@AcmeCorp\n12,500 Followers\n\nBio: Building the future of enterprise AI.",
            ),
            "twitter.com": _scrape_ok(
                "https://twitter.com/acme",
                "# @acme\n\n5.2K Followers\n\nEnterprise AI platform.",
            ),
        }
    )

    records = await run_social(_req("social"), crawler)

    assert len(records) >= 2
    platforms = {r["platform"] for r in records}
    assert "linkedin" in platforms
    assert "twitter" in platforms


# ---------------------------------------------------------------------------
# Locations runner
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_locations_runner_extracts_addresses() -> None:
    from scout.core.use_cases.runners.locations import run_locations

    crawler = _mock_crawler(
        {
            "/locations": _scrape_ok(
                "https://www.acme.com/locations",
                "# Our Offices\n\n"
                "## San Francisco\n123 Market St, San Francisco, CA 94105\n(415) 555-1234\n\n"
                "## New York\n456 Broadway Ave, New York, NY 10013\n(212) 555-5678\n",
            ),
        }
    )

    records = await run_locations(_req("locations"), crawler)

    assert len(records) >= 2
    assert all(r["record_type"] == "location" for r in records)
    addresses = [r["address"] for r in records]
    assert any("Market" in a for a in addresses)
    assert any("Broadway" in a for a in addresses)


@pytest.mark.asyncio
async def test_locations_runner_returns_fallback_when_no_addresses() -> None:
    from scout.core.use_cases.runners.locations import run_locations

    crawler = _mock_crawler(
        {
            "/locations": _scrape_ok(
                "https://www.acme.com/locations",
                "# Our Locations\n\nWe have offices worldwide. Contact us for details.",
            ),
        }
    )

    records = await run_locations(_req("locations"), crawler)
    assert len(records) == 1
    assert records[0]["record_type"] == "location"
    assert "locations page" in records[0]["name"].lower()
