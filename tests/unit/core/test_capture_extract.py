"""Tests for capture structuring — turn an already-fetched (human-cleared)
page into clean markdown + optional typed records WITHOUT re-fetching.

The critical guarantee: structuring runs the captured HTML through Crawl4AI's
`raw://` scheme, never the live URL — re-fetching a cleared page would
re-trigger the anti-bot wall the human just solved.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

from crawl4ai.extraction_strategy import ExtractionStrategy

from scout.core.capture_extract import structure_capture


def _strategy_mock() -> MagicMock:
    """Mock that passes CrawlerRunConfig's isinstance check."""
    return create_autospec(ExtractionStrategy, instance=True)


def _result(*, success=True, markdown="", extracted=None):
    r = MagicMock()
    r.success = success
    r.url = "raw://"
    r.markdown = markdown
    r.fit_markdown = markdown
    r.extracted_content = extracted
    r.metadata = {"title": "Cleared Page", "description": "", "language": "en"}
    r.error_message = "" if success else "boom"
    return r


@pytest.mark.asyncio
async def test_structure_capture_produces_clean_markdown():
    """Raw HTML, no schema → success with clean markdown, no records."""
    html = "<html><body><h1>615 Roswell Rentals</h1></body></html>"
    mock = _result(markdown="# 615 Roswell Rentals")

    with patch("scout.core.capture_extract.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.arun.return_value = mock
        MockCrawler.return_value.__aenter__.return_value = instance

        resp = await structure_capture(html, source_url="https://zillow.com/roswell")

    assert resp.success is True
    assert "Roswell" in resp.markdown
    assert resp.records == []
    assert resp.source_url == "https://zillow.com/roswell"
    assert resp.word_count > 0


@pytest.mark.asyncio
async def test_structure_capture_never_refetches_uses_raw_scheme():
    """The decisive guarantee: arun is called with `raw://`+HTML, NOT the live
    URL — so a cleared page is structured without re-triggering the wall."""
    html = "<html><body><p>cleared content</p></body></html>"
    mock = _result(markdown="cleared content")

    with patch("scout.core.capture_extract.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.arun.return_value = mock
        MockCrawler.return_value.__aenter__.return_value = instance

        await structure_capture(html, source_url="https://zillow.com/roswell")

    called_url = instance.arun.call_args.args[0]
    assert called_url.startswith("raw://")
    assert html in called_url
    assert "zillow.com" not in called_url  # never the live URL


@pytest.mark.asyncio
async def test_structure_capture_with_css_schema_returns_records():
    """A CSS schema yields typed per-item records (no LLM needed)."""
    html = "<ul><li>A</li><li>B</li></ul>"
    css_schema = {
        "name": "items",
        "baseSelector": "li",
        "fields": [{"name": "name", "selector": "li", "type": "text"}],
    }
    mock = _result(
        markdown="A B",
        extracted=json.dumps([{"name": "A"}, {"name": "B"}]),
    )

    with patch("scout.core.capture_extract.AsyncWebCrawler") as MockCrawler:
        with patch(
            "scout.core.capture_extract.JsonCssExtractionStrategy",
            return_value=_strategy_mock(),
        ) as MockCss:
            instance = AsyncMock()
            instance.arun.return_value = mock
            MockCrawler.return_value.__aenter__.return_value = instance

            resp = await structure_capture(html, css_schema=css_schema)

    assert resp.success is True
    assert resp.record_count == 2
    assert resp.records[0]["name"] == "A"
    MockCss.assert_called_once_with(schema=css_schema)


@pytest.mark.asyncio
async def test_structure_capture_surfaces_crawl_failure():
    """result.success False → honest failure, error surfaced, not faked."""
    mock = _result(success=False)

    with patch("scout.core.capture_extract.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.arun.return_value = mock
        MockCrawler.return_value.__aenter__.return_value = instance

        resp = await structure_capture("<html></html>")

    assert resp.success is False
    assert resp.error


@pytest.mark.asyncio
async def test_structure_capture_handles_exception():
    """A thrown crawler error degrades honestly to success=False."""
    with patch("scout.core.capture_extract.AsyncWebCrawler") as MockCrawler:
        MockCrawler.return_value.__aenter__.side_effect = RuntimeError("crawl boom")

        resp = await structure_capture("<html></html>")

    assert resp.success is False
    assert "crawl boom" in resp.error


@pytest.mark.asyncio
async def test_structure_capture_empty_html_is_honest_failure():
    """Empty capture → immediate honest failure, no crawl attempted."""
    resp = await structure_capture("   ")
    assert resp.success is False
    assert "empty" in resp.error.lower()
