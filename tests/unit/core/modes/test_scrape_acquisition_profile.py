"""Tests for optional acquisition metadata on the shared /scrape primitive."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scout.core.modes.scrape import scrape
from scout.core.types import ScrapeRequest


@pytest.mark.asyncio
async def test_scrape_default_keeps_acquisition_metadata_off() -> None:
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.url = "https://example.com"
    mock_result.markdown = "# Example Domain\nUseful content"
    mock_result.html = "<main><h1>Example Domain</h1><p>Useful content</p></main>"
    mock_result.links = {"internal": [], "external": []}
    mock_result.metadata = {"title": "Example Domain", "description": "", "language": "en"}
    mock_result.screenshot = None

    with patch("scout.core.modes.scrape.AsyncWebCrawler") as mock_crawler:
        instance = AsyncMock()
        instance.arun.return_value = mock_result
        mock_crawler.return_value.__aenter__.return_value = instance

        resp = await scrape(ScrapeRequest(url="https://example.com"))

    assert resp.success is True
    assert resp.markdown
    assert resp.raw_markdown == ""
    assert resp.clean_markdown == ""
    assert resp.acquisition is None


@pytest.mark.asyncio
async def test_scrape_opt_in_acquisition_metadata_is_nested_and_explainable() -> None:
    raw_markdown = "# Product updates\nCookie preferences\nAccept all cookies\nAI Search launched"
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.url = "https://example.com/product"
    mock_result.markdown = raw_markdown
    mock_result.html = "<main><h1>Product updates</h1><p>AI Search launched</p></main>"
    mock_result.links = {"internal": [{"href": "https://example.com/docs"}], "external": []}
    mock_result.metadata = {"title": "Product updates", "description": "", "language": "en"}
    mock_result.screenshot = None

    with patch("scout.core.modes.scrape.AsyncWebCrawler") as mock_crawler:
        instance = AsyncMock()
        instance.arun.return_value = mock_result
        mock_crawler.return_value.__aenter__.return_value = instance

        req = ScrapeRequest(
            url="https://example.com/product",
            quality_analysis=True,
            cleanup=True,
            expected_markers=["AI Search"],
            recommend_collector=True,
            source_id="constructor-product",
            use_js=True,
        )
        resp = await scrape(req)

    assert resp.success is True
    assert resp.markdown == raw_markdown
    assert resp.raw_markdown == raw_markdown
    assert "Accept all cookies" not in resp.clean_markdown
    assert resp.acquisition is not None
    assert resp.acquisition.schema_version == "acquisition_metadata.v1"
    assert resp.model_dump(by_alias=True)["acquisition"]["schema"] == "acquisition_metadata.v1"
    assert resp.acquisition.source_id == "constructor-product"
    assert resp.acquisition.provider == "crawl4ai"
    assert resp.acquisition.content_hash
    assert resp.acquisition.markers_found == ["AI Search"]
    assert resp.acquisition.marker_score == 1.0
    assert "expected_markers_found" in resp.acquisition.quality_reasons
    assert resp.acquisition.recommended_collector == "scout_scrape"
    assert resp.acquisition.recommended_collector_reason == "browser_rendered_page"
    assert resp.acquisition.boilerplate_removed > 0
    assert "cookie_preferences" in resp.acquisition.cleanup_rules_applied


@pytest.mark.asyncio
async def test_scrape_feed_url_recommends_rss_without_new_endpoint() -> None:
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.url = "https://openai.com/news/rss.xml"
    mock_result.markdown = "<rss><channel><title>OpenAI News</title></channel></rss>"
    mock_result.html = ""
    mock_result.links = {"internal": [], "external": []}
    mock_result.metadata = {"title": "", "description": "", "language": ""}
    mock_result.screenshot = None

    with patch("scout.core.modes.scrape.AsyncWebCrawler") as mock_crawler:
        instance = AsyncMock()
        instance.arun.return_value = mock_result
        mock_crawler.return_value.__aenter__.return_value = instance

        resp = await scrape(
            ScrapeRequest(
                url="https://openai.com/news/rss.xml",
                quality_analysis=True,
                recommend_collector=True,
            )
        )

    assert resp.acquisition is not None
    assert resp.acquisition.recommended_collector == "rss_feed"
    assert resp.acquisition.recommended_collector_reason == "feed_like_url"
