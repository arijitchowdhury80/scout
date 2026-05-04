"""Tests for map mode — URL discovery without content extraction."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from scout.core.modes.map import map_urls
from scout.core.types import MapRequest, MapResponse


def _make_url_result(url: str) -> MagicMock:
    r = MagicMock()
    r.success = True
    r.url = url
    r.markdown = ""
    r.fit_markdown = ""
    r.metadata = {}
    return r


@pytest.mark.asyncio
async def test_map_returns_url_list():
    results = [_make_url_result(u) for u in ["https://example.com", "https://example.com/about", "https://example.com/contact"]]

    with patch("scout.core.modes.map.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        async def fake_gen(urls, config):
            for r in results:
                yield r
        instance.arun_many.return_value = fake_gen([], None)
        MockCrawler.return_value.__aenter__.return_value = instance

        with patch("scout.core.modes.map.BFSDeepCrawlStrategy"):
            req = MapRequest(url="https://example.com")
            resp = await map_urls(req)

    assert resp.success is True
    assert resp.total >= 0
    assert isinstance(resp.urls, list)
    assert resp.start_url == "https://example.com"


@pytest.mark.asyncio
async def test_map_handles_exception():
    with patch("scout.core.modes.map.AsyncWebCrawler") as MockCrawler:
        MockCrawler.return_value.__aenter__.side_effect = RuntimeError("timeout")
        req = MapRequest(url="https://example.com")
        resp = await map_urls(req)

    assert resp.success is False
    assert "timeout" in resp.error
    assert resp.urls == []
