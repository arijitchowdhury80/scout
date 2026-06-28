"""Tests for Crawl4AI-over-CDP acquisition — attach the CORE engine to an
already-open (human-cleared) browser tab and structure it WITHOUT navigating.

This keeps Crawl4AI as Scout's engine even on the hardest human-assisted path:
the human clears the wall in real Chrome, then Crawl4AI attaches over CDP and
drives THAT tab (js_only=True → no goto → no wall re-trigger), producing clean
markdown + typed records through the same pipeline used everywhere else.

Verified contract (read receipt):
- BrowserConfig(browser_mode="cdp", cdp_url=...) → connect_over_cdp
- get_page adopts the existing tab matching the url (browser_manager.py:1078)
- CrawlerRunConfig(js_only=True) skips page.goto (async_crawler_strategy.py:666)
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

from crawl4ai.extraction_strategy import ExtractionStrategy

from scout.core.cdp_acquire import acquire_open_page


def _strategy_mock() -> MagicMock:
    return create_autospec(ExtractionStrategy, instance=True)


def _result(*, success=True, markdown="", extracted=None):
    r = MagicMock()
    r.success = success
    r.url = "https://zillow.com/roswell"
    r.markdown = markdown
    r.fit_markdown = markdown
    r.html = "<html><body>Roswell Rentals</body></html>"
    r.extracted_content = extracted
    r.metadata = {"title": "Roswell Rentals", "description": "", "language": "en"}
    r.error_message = "" if success else "boom"
    return r


@pytest.mark.asyncio
async def test_acquire_attaches_over_cdp_and_never_navigates():
    """The two load-bearing guarantees: BrowserConfig targets the CDP endpoint,
    and arun runs with js_only=True so the cleared tab is NOT re-navigated."""
    captured = {}

    def fake_browser_config(**kwargs):
        captured["browser"] = kwargs
        return MagicMock()

    def fake_run_config(**kwargs):
        captured["run"] = kwargs
        cfg = MagicMock()
        cfg.__dict__.update(kwargs)
        return cfg

    with (
        patch("scout.core.cdp_acquire.AsyncWebCrawler") as MockCrawler,
        patch("scout.core.cdp_acquire.BrowserConfig", side_effect=fake_browser_config),
        patch("scout.core.cdp_acquire.CrawlerRunConfig", side_effect=fake_run_config),
    ):
        instance = AsyncMock()
        instance.arun.return_value = _result(markdown="# Roswell Rentals")
        MockCrawler.return_value.__aenter__.return_value = instance

        resp = await acquire_open_page("http://127.0.0.1:49321", "https://zillow.com/roswell")

    assert captured["browser"].get("browser_mode") == "cdp"
    assert captured["browser"].get("cdp_url") == "http://127.0.0.1:49321"
    assert captured["run"].get("js_only") is True  # never re-navigate the cleared tab
    # arun is told which tab to adopt (get_page matches by url)
    assert instance.arun.call_args.args[0] == "https://zillow.com/roswell"
    assert resp.success is True
    assert "Roswell" in resp.markdown
    assert "Roswell Rentals" in resp.raw_html


@pytest.mark.asyncio
async def test_acquire_with_css_schema_returns_records():
    mock = _result(markdown="A B", extracted=json.dumps([{"addr": "A"}, {"addr": "B"}]))
    css_schema = {"name": "x", "baseSelector": "li", "fields": []}

    with (
        patch("scout.core.cdp_acquire.AsyncWebCrawler") as MockCrawler,
        patch(
            "scout.core.cdp_acquire.JsonCssExtractionStrategy", return_value=_strategy_mock()
        ) as MockCss,
    ):
        instance = AsyncMock()
        instance.arun.return_value = mock
        MockCrawler.return_value.__aenter__.return_value = instance

        resp = await acquire_open_page("http://127.0.0.1:1", "https://x.com", css_schema=css_schema)

    assert resp.record_count == 2
    assert resp.records[0]["addr"] == "A"
    MockCss.assert_called_once_with(schema=css_schema)


@pytest.mark.asyncio
async def test_acquire_empty_cdp_url_is_honest_failure():
    resp = await acquire_open_page("", "https://x.com")
    assert resp.success is False
    assert "cdp" in resp.error.lower()


@pytest.mark.asyncio
async def test_acquire_surfaces_crawl_failure():
    with patch("scout.core.cdp_acquire.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.arun.return_value = _result(success=False)
        MockCrawler.return_value.__aenter__.return_value = instance

        resp = await acquire_open_page("http://127.0.0.1:1", "https://x.com")

    assert resp.success is False
    assert resp.error


@pytest.mark.asyncio
async def test_acquire_handles_exception():
    with patch("scout.core.cdp_acquire.AsyncWebCrawler") as MockCrawler:
        MockCrawler.return_value.__aenter__.side_effect = RuntimeError("cdp down")

        resp = await acquire_open_page("http://127.0.0.1:1", "https://x.com")

    assert resp.success is False
    assert "cdp down" in resp.error
