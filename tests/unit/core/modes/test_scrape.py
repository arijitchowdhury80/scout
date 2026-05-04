"""Tests for scrape mode — single URL fetch."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from scout.core.modes.scrape import scrape
from scout.core.types import ScrapeRequest, ScrapeResponse, ScoutFormats


@pytest.mark.asyncio
async def test_scrape_returns_markdown_on_success():
    """scrape() returns clean markdown when crawl succeeds."""
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.url = "https://example.com"
    mock_result.markdown = "# Hello World\n\nThis is content."
    mock_result.fit_markdown = "# Hello World\n\nThis is content."
    mock_result.html = "<h1>Hello</h1>"
    mock_result.links = {"internal": [{"href": "https://example.com/about"}], "external": []}
    mock_result.metadata = {"title": "Example", "description": "A site", "language": "en"}
    mock_result.screenshot = None

    with patch("scout.core.modes.scrape.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.arun.return_value = mock_result
        MockCrawler.return_value.__aenter__.return_value = instance

        req = ScrapeRequest(url="https://example.com")
        resp = await scrape(req)

    assert resp.success is True
    assert "Hello World" in resp.markdown
    assert resp.url == "https://example.com"
    assert resp.error == ""


@pytest.mark.asyncio
async def test_scrape_returns_failure_on_crawl_error():
    """scrape() returns success=False when crawl4ai reports failure."""
    mock_result = MagicMock()
    mock_result.success = False
    mock_result.url = "https://example.com"
    mock_result.error_message = "Connection refused"

    with patch("scout.core.modes.scrape.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.arun.return_value = mock_result
        MockCrawler.return_value.__aenter__.return_value = instance

        req = ScrapeRequest(url="https://example.com")
        resp = await scrape(req)

    assert resp.success is False
    assert "Connection refused" in resp.error
    assert resp.markdown == ""


@pytest.mark.asyncio
async def test_scrape_includes_links():
    """scrape() extracts internal links from the crawl result."""
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.url = "https://example.com"
    mock_result.markdown = "content"
    mock_result.fit_markdown = "content"
    mock_result.html = ""
    mock_result.links = {
        "internal": [{"href": "https://example.com/about"}, {"href": "https://example.com/contact"}],
        "external": [{"href": "https://google.com"}],
    }
    mock_result.metadata = {"title": "", "description": "", "language": ""}
    mock_result.screenshot = None

    with patch("scout.core.modes.scrape.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.arun.return_value = mock_result
        MockCrawler.return_value.__aenter__.return_value = instance

        req = ScrapeRequest(url="https://example.com")
        resp = await scrape(req)

    assert "https://example.com/about" in resp.links
    assert "https://example.com/contact" in resp.links


@pytest.mark.asyncio
async def test_scrape_includes_screenshot_when_requested():
    """scrape() returns screenshot_base64 when formats includes SCREENSHOT."""
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.url = "https://example.com"
    mock_result.markdown = "content"
    mock_result.fit_markdown = "content"
    mock_result.html = ""
    mock_result.links = {"internal": [], "external": []}
    mock_result.metadata = {"title": "", "description": "", "language": ""}
    mock_result.screenshot = "iVBORw0KGgo="  # fake base64

    with patch("scout.core.modes.scrape.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.arun.return_value = mock_result
        MockCrawler.return_value.__aenter__.return_value = instance

        req = ScrapeRequest(url="https://example.com", formats=[ScoutFormats.MARKDOWN, ScoutFormats.SCREENSHOT])
        resp = await scrape(req)

    assert resp.screenshot_base64 == "iVBORw0KGgo="


@pytest.mark.asyncio
async def test_scrape_handles_exception_gracefully():
    """scrape() catches unexpected exceptions and returns failure response."""
    with patch("scout.core.modes.scrape.AsyncWebCrawler") as MockCrawler:
        MockCrawler.return_value.__aenter__.side_effect = RuntimeError("Browser crashed")

        req = ScrapeRequest(url="https://example.com")
        resp = await scrape(req)

    assert resp.success is False
    assert "Browser crashed" in resp.error


@pytest.mark.asyncio
async def test_scrape_metadata_includes_token_estimate():
    """scrape() always returns a token_estimate in metadata."""
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.url = "https://example.com"
    mock_result.markdown = "word " * 500  # 500 words
    mock_result.fit_markdown = "word " * 500
    mock_result.html = ""
    mock_result.links = {"internal": [], "external": []}
    mock_result.metadata = {"title": "Test", "description": "", "language": "en"}
    mock_result.screenshot = None

    with patch("scout.core.modes.scrape.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.arun.return_value = mock_result
        MockCrawler.return_value.__aenter__.return_value = instance

        req = ScrapeRequest(url="https://example.com")
        resp = await scrape(req)

    assert resp.metadata.token_estimate > 0
    assert resp.metadata.word_count > 0
