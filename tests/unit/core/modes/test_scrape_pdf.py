"""Tests for PDF routing in scrape mode — FX-11 Build 1."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from scout.core.modes.scrape import scrape
from scout.core.types import ScrapeRequest

FIXTURE = Path(__file__).parent.parent.parent.parent / "fixtures" / "sample.pdf"


@pytest.mark.asyncio
async def test_scrape_pdf_url_returns_extracted_text_not_crawl4ai():
    """A .pdf URL is routed to the pypdf path instead of Crawl4AI's browser."""
    pdf_bytes = FIXTURE.read_bytes()

    with (
        patch("scout.core.modes.scrape.fetch_pdf_bytes", new=AsyncMock(return_value=pdf_bytes)),
        patch("scout.core.modes.scrape.AsyncWebCrawler") as MockCrawler,
    ):
        req = ScrapeRequest(url="https://example.com/sample.pdf")
        resp = await scrape(req)

        MockCrawler.assert_not_called()

    assert resp.success is True
    assert "Hello Scout PDF" in resp.markdown
    assert resp.provider == "pdf"
    assert resp.pdf is not None
    assert resp.pdf.page_count == 1
    assert resp.pdf.title == "Scout PDF Fixture"
    assert resp.error == ""
    assert resp.duration_ms >= 0


@pytest.mark.asyncio
async def test_scrape_pdf_url_download_failure_returns_clean_error():
    """A PDF URL that fails to download returns success=False with a real error, not a crash."""
    with patch(
        "scout.core.modes.scrape.fetch_pdf_bytes",
        new=AsyncMock(side_effect=RuntimeError("connection refused")),
    ):
        req = ScrapeRequest(url="https://example.com/missing.pdf")
        resp = await scrape(req)

    assert resp.success is False
    assert resp.provider == "pdf"
    assert "connection refused" in resp.error
    assert resp.pdf is None


@pytest.mark.asyncio
async def test_scrape_non_pdf_url_still_uses_crawl4ai():
    """Non-PDF URLs are unaffected — still routed through Crawl4AI as before."""
    from unittest.mock import MagicMock

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.url = "https://example.com"
    mock_result.markdown = "# Hello"
    mock_result.fit_markdown = "# Hello"
    mock_result.html = ""
    mock_result.links = {"internal": [], "external": []}
    mock_result.metadata = {"title": "Example"}
    mock_result.screenshot = None

    with patch("scout.core.modes.scrape.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.arun.return_value = mock_result
        MockCrawler.return_value.__aenter__.return_value = instance

        req = ScrapeRequest(url="https://example.com")
        resp = await scrape(req)

    assert resp.provider == "crawl4ai"
    assert resp.pdf is None
