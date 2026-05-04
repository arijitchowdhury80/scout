"""Tests for ScoutCrawler — verifies delegation to mode functions."""
from unittest.mock import AsyncMock, patch

import pytest

from scout.core.crawler import ScoutCrawler
from scout.core.types import (
    CrawlRequest,
    CrawlResponse,
    ExtractRequest,
    ExtractResponse,
    MapRequest,
    MapResponse,
    ScoutMetadata,
    ScrapeRequest,
    ScrapeResponse,
    ScreenshotRequest,
    ScreenshotResponse,
)


def _meta(url: str) -> ScoutMetadata:
    return ScoutMetadata(url=url, crawled_at="2026-05-03T00:00:00Z")


@pytest.fixture
def scrape_req() -> ScrapeRequest:
    return ScrapeRequest(url="https://example.com")


@pytest.fixture
def crawl_req() -> CrawlRequest:
    return CrawlRequest(url="https://example.com")


@pytest.fixture
def extract_req() -> ExtractRequest:
    return ExtractRequest(
        url="https://example.com",
        schema={"name": "str"},
        instruction="extract name",
    )


@pytest.fixture
def map_req() -> MapRequest:
    return MapRequest(url="https://example.com")


@pytest.fixture
def screenshot_req() -> ScreenshotRequest:
    return ScreenshotRequest(url="https://example.com")


async def test_scrape_delegates_to_scrape_mode(scrape_req: ScrapeRequest) -> None:
    mock_response = ScrapeResponse(
        success=True, url=scrape_req.url, metadata=_meta(scrape_req.url), duration_ms=10
    )
    with patch("scout.core.crawler._scrape", new_callable=AsyncMock, return_value=mock_response) as mock:
        result = await ScoutCrawler().scrape(scrape_req)
    mock.assert_called_once_with(scrape_req)
    assert result is mock_response


async def test_crawl_delegates_to_crawl_mode(crawl_req: CrawlRequest) -> None:
    mock_response = CrawlResponse(
        success=True, start_url=crawl_req.url, total_pages=0, duration_ms=10
    )
    with patch("scout.core.crawler._crawl", new_callable=AsyncMock, return_value=mock_response) as mock:
        result = await ScoutCrawler().crawl(crawl_req)
    mock.assert_called_once_with(crawl_req)
    assert result is mock_response


async def test_extract_passes_llm_key(extract_req: ExtractRequest) -> None:
    mock_response = ExtractResponse(
        success=True, url=extract_req.url, metadata=_meta(extract_req.url), duration_ms=10
    )
    with patch("scout.core.crawler._extract", new_callable=AsyncMock, return_value=mock_response) as mock:
        result = await ScoutCrawler(llm_api_key="test-key").extract(extract_req)
    mock.assert_called_once_with(extract_req, "test-key")
    assert result is mock_response


async def test_map_delegates_to_map_mode(map_req: MapRequest) -> None:
    mock_response = MapResponse(
        success=True, start_url=map_req.url, total=0, duration_ms=10
    )
    with patch("scout.core.crawler._map_urls", new_callable=AsyncMock, return_value=mock_response) as mock:
        result = await ScoutCrawler().map_urls(map_req)
    mock.assert_called_once_with(map_req)
    assert result is mock_response


async def test_screenshot_delegates_to_screenshot_mode(screenshot_req: ScreenshotRequest) -> None:
    mock_response = ScreenshotResponse(
        success=True, url=screenshot_req.url, width=1280, height=800, duration_ms=10
    )
    with patch("scout.core.crawler._screenshot", new_callable=AsyncMock, return_value=mock_response) as mock:
        result = await ScoutCrawler().screenshot(screenshot_req)
    mock.assert_called_once_with(screenshot_req)
    assert result is mock_response
