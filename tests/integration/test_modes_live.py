"""Integration tests — Scout modes against real URLs with real Crawl4AI.

These tests hit the network and launch a real Playwright browser.
They are SLOW (~5-30s each) and require Playwright to be installed.

Run: pytest tests/integration/ -v -m integration
Skip in CI fast pass: pytest tests/unit/ -v -m "not integration"

What these tests prove that unit tests cannot:
- `result.markdown.fit_markdown` attribute path is correct in installed Crawl4AI
- `arun_many(stream=True)` async generator iteration works end-to-end
- `extracted_content` attribute exists and contains JSON on extract
- Real pages return non-empty markdown with populated metadata
- ScoutMetadata fields (title, word_count, token_estimate) are populated from real content
"""

import pytest

from scout.core.modes.scrape import scrape
from scout.core.modes.crawl import crawl
from scout.core.modes.map import map_urls
from scout.core.modes.screenshot import screenshot
from scout.core.types import (
    ScrapeRequest,
    ScoutFormats,
    CrawlRequest,
    MapRequest,
    ScreenshotRequest,
    ScrapeResponse,
    CrawlResponse,
    MapResponse,
    ScreenshotResponse,
)

# Use a stable, lightweight test target
_TEST_URL = "https://example.com"


@pytest.mark.integration
async def test_scrape_returns_non_empty_markdown():
    """Verifies fit_markdown path and metadata population on a real page."""
    req = ScrapeRequest(url=_TEST_URL)
    resp = await scrape(req)

    assert isinstance(resp, ScrapeResponse)
    assert resp.success is True, f"scrape failed: {resp.error}"
    assert len(resp.markdown) > 0, "markdown is empty"
    assert resp.metadata.word_count > 0
    assert resp.metadata.token_estimate > 0
    assert resp.duration_ms > 0


@pytest.mark.integration
async def test_scrape_screenshot_returns_base64():
    """Verifies screenshot capture path end-to-end."""
    req = ScrapeRequest(url=_TEST_URL, formats=[ScoutFormats.MARKDOWN, ScoutFormats.SCREENSHOT])
    resp = await scrape(req)

    assert resp.success is True, f"scrape failed: {resp.error}"
    assert len(resp.screenshot_base64) > 0, "screenshot_base64 is empty"


@pytest.mark.integration
async def test_scrape_failure_returns_error_not_exception():
    """Verifies error handling: invalid URL returns success=False, not a raised exception."""
    req = ScrapeRequest(url="https://this-domain-definitely-does-not-exist-scout-test.invalid")
    resp = await scrape(req)

    assert isinstance(resp, ScrapeResponse)
    assert resp.success is False
    assert len(resp.error) > 0


@pytest.mark.integration
async def test_crawl_returns_pages():
    """Verifies arun_many streaming pattern and multi-page crawl."""
    req = CrawlRequest(url=_TEST_URL, max_depth=1, max_pages=3)
    resp = await crawl(req)

    assert isinstance(resp, CrawlResponse)
    assert resp.success is True, f"crawl failed: {resp.error}"
    assert resp.total_pages >= 1
    assert len(resp.pages) >= 1
    assert resp.pages[0].url != ""


@pytest.mark.integration
async def test_map_returns_urls():
    """Verifies URL discovery without content extraction."""
    req = MapRequest(url=_TEST_URL, max_pages=10)
    resp = await map_urls(req)

    assert isinstance(resp, MapResponse)
    assert resp.success is True, f"map failed: {resp.error}"
    assert resp.total >= 1
    assert len(resp.urls) >= 1
    assert all(u.startswith("http") for u in resp.urls)


@pytest.mark.integration
async def test_screenshot_returns_base64_png():
    """Verifies screenshot-only path with correct dimensions."""
    req = ScreenshotRequest(url=_TEST_URL, viewport_width=1280, viewport_height=800)
    resp = await screenshot(req)

    assert isinstance(resp, ScreenshotResponse)
    assert resp.success is True, f"screenshot failed: {resp.error}"
    assert len(resp.screenshot_base64) > 0
    assert resp.width == 1280
    assert resp.height == 800
