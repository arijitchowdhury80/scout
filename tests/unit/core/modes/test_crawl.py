"""Tests for crawl mode — BFSDeepCrawlStrategy via crawler.arun()."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from scout.core.modes.crawl import crawl
from scout.core.types import CrawlRequest, CrawlResponse


def _make_crawl_result(url: str, markdown: str = "page content", depth: int = 0) -> MagicMock:
    """Simulate a CrawlResult yielded by BFSDeepCrawlStrategy in stream mode."""
    r = MagicMock()
    r.success = True
    r.url = url
    r.markdown = markdown
    r.metadata = {"title": "Test Page", "description": "", "language": "en", "depth": depth}
    r.error_message = ""
    return r


async def _async_gen(*items):
    """Helper: turn items into an async generator (simulates strategy stream)."""
    for item in items:
        yield item


@pytest.mark.asyncio
async def test_crawl_returns_pages_from_strategy_stream():
    """BFSDeepCrawlStrategy yields two results → CrawlResponse has two pages."""
    page1 = _make_crawl_result("https://example.com", depth=0)
    page2 = _make_crawl_result("https://example.com/about", depth=1)

    with patch("scout.core.modes.crawl.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        # crawler.arun() returns a coroutine that resolves to an async generator
        instance.arun = AsyncMock(return_value=_async_gen(page1, page2))
        MockCrawler.return_value.__aenter__.return_value = instance

        req = CrawlRequest(url="https://example.com", max_depth=2, max_pages=10)
        resp = await crawl(req)

    assert resp.success is True
    assert resp.total_pages == 2
    assert len(resp.pages) == 2
    assert resp.pages[0].url == "https://example.com"
    assert resp.pages[1].url == "https://example.com/about"
    assert resp.pages[0].success is True


@pytest.mark.asyncio
async def test_crawl_handles_exception():
    """Exception during crawl → success=False, empty pages, error populated."""
    with patch("scout.core.modes.crawl.AsyncWebCrawler") as MockCrawler:
        MockCrawler.return_value.__aenter__.side_effect = RuntimeError("Browser crashed")

        req = CrawlRequest(url="https://example.com")
        resp = await crawl(req)

    assert resp.success is False
    assert "Browser crashed" in resp.error
    assert resp.pages == []
    assert resp.total_pages == 0


@pytest.mark.asyncio
async def test_crawl_response_has_correct_start_url():
    """start_url in response matches request URL regardless of crawl results."""
    with patch("scout.core.modes.crawl.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.arun = AsyncMock(return_value=_async_gen())  # empty stream
        MockCrawler.return_value.__aenter__.return_value = instance

        req = CrawlRequest(url="https://nike.com")
        resp = await crawl(req)

    assert resp.start_url == "https://nike.com"


@pytest.mark.asyncio
async def test_crawl_handles_failed_page_in_stream():
    """Strategy may yield a failed result — included in pages with success=False."""
    failed = MagicMock()
    failed.success = False
    failed.url = "https://example.com/404"
    failed.markdown = ""
    failed.metadata = {"title": "", "description": "", "language": "", "depth": 1}
    failed.error_message = "404 Not Found"

    with patch("scout.core.modes.crawl.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.arun = AsyncMock(return_value=_async_gen(failed))
        MockCrawler.return_value.__aenter__.return_value = instance

        req = CrawlRequest(url="https://example.com", max_depth=1, max_pages=5)
        resp = await crawl(req)

    assert resp.success is True  # crawl itself succeeded
    assert resp.total_pages == 1
    assert resp.pages[0].success is False
    assert "404" in resp.pages[0].error
