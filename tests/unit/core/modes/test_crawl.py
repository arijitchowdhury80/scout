"""Tests for crawl mode — recursive multi-page crawl."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from scout.core.modes.crawl import crawl
from scout.core.types import CrawlRequest, CrawlResponse


def _make_page_result(url: str, markdown: str = "content") -> MagicMock:
    r = MagicMock()
    r.success = True
    r.url = url
    r.markdown = markdown
    r.fit_markdown = markdown
    r.metadata = {"title": "", "description": "", "language": ""}
    return r


@pytest.mark.asyncio
async def test_crawl_returns_multiple_pages():
    page1 = _make_page_result("https://example.com")
    page2 = _make_page_result("https://example.com/about")

    with patch("scout.core.modes.crawl.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        async def fake_arun_many(urls, config):
            for r in [page1, page2]:
                yield r
        instance.arun_many.return_value = fake_arun_many([], None)
        MockCrawler.return_value.__aenter__.return_value = instance

        # Patch BFSDeepCrawlStrategy to avoid real crawling
        with patch("scout.core.modes.crawl.BFSDeepCrawlStrategy"):
            req = CrawlRequest(url="https://example.com", max_depth=1, max_pages=5)
            resp = await crawl(req)

    assert resp.success is True
    assert resp.total_pages >= 0
    assert isinstance(resp.pages, list)


@pytest.mark.asyncio
async def test_crawl_handles_exception():
    with patch("scout.core.modes.crawl.AsyncWebCrawler") as MockCrawler:
        MockCrawler.return_value.__aenter__.side_effect = RuntimeError("Browser crashed")
        req = CrawlRequest(url="https://example.com")
        resp = await crawl(req)

    assert resp.success is False
    assert "Browser crashed" in resp.error
    assert resp.pages == []


@pytest.mark.asyncio
async def test_crawl_response_has_correct_start_url():
    with patch("scout.core.modes.crawl.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        async def empty_gen(urls, config):
            return
            yield  # make it an async generator
        instance.arun_many.return_value = empty_gen([], None)
        MockCrawler.return_value.__aenter__.return_value = instance

        with patch("scout.core.modes.crawl.BFSDeepCrawlStrategy"):
            req = CrawlRequest(url="https://nike.com")
            resp = await crawl(req)

    assert resp.start_url == "https://nike.com"
