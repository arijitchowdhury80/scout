"""Tests for map mode — sitemap-first + BFS fallback URL discovery."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from scout.core.modes.map import map_urls
from scout.core.types import MapRequest


# ── Sitemap path ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_map_uses_sitemap_when_available():
    """Primary path: sitemap returns enough URLs → BFS fallback not called."""
    sitemap_urls = [f"https://example.com/page-{i}" for i in range(10)]

    with patch("scout.core.modes.map.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.aseed_urls = AsyncMock(return_value=sitemap_urls)
        MockCrawler.return_value.__aenter__.return_value = instance

        req = MapRequest(url="https://example.com", max_pages=50)
        resp = await map_urls(req)

    assert resp.success is True
    assert resp.total == 10
    assert resp.urls == sitemap_urls
    assert resp.start_url == "https://example.com"
    # BFS fallback (arun) should NOT have been called
    instance.arun.assert_not_called()


@pytest.mark.asyncio
async def test_map_applies_max_pages_cap_to_sitemap_results():
    """Sitemap may return more URLs than max_pages — cap is applied."""
    sitemap_urls = [f"https://example.com/page-{i}" for i in range(20)]

    with patch("scout.core.modes.map.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.aseed_urls = AsyncMock(return_value=sitemap_urls)
        MockCrawler.return_value.__aenter__.return_value = instance

        req = MapRequest(url="https://example.com", max_pages=5)
        resp = await map_urls(req)

    assert resp.success is True
    assert resp.total == 5
    assert len(resp.urls) == 5


@pytest.mark.asyncio
async def test_map_applies_url_pattern_filter_to_sitemap_results():
    """url_pattern filters sitemap URLs before returning."""
    sitemap_urls = [
        "https://example.com/blog/post-1",
        "https://example.com/products/widget",
        "https://example.com/blog/post-2",
    ]

    with patch("scout.core.modes.map.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.aseed_urls = AsyncMock(return_value=sitemap_urls)
        MockCrawler.return_value.__aenter__.return_value = instance

        req = MapRequest(url="https://example.com", url_pattern="/blog/")
        resp = await map_urls(req)

    assert resp.success is True
    assert resp.total == 2
    assert all("/blog/" in u for u in resp.urls)


# ── BFS fallback path ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_map_falls_back_to_bfs_when_sitemap_sparse():
    """When sitemap returns fewer than threshold URLs, BFS fallback runs."""
    # Sitemap returns only 2 URLs — below _SITEMAP_MIN_THRESHOLD (5)
    sparse_sitemap = ["https://example.com/sitemap-index.xml", "https://example.com/"]

    # BFS arun result for the seed URL — has two internal links
    bfs_result = MagicMock()
    bfs_result.success = True
    bfs_result.url = "https://example.com"
    bfs_result.links = {
        "internal": [
            {"href": "https://example.com/about"},
            {"href": "https://example.com/contact"},
        ]
    }

    with patch("scout.core.modes.map.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        # First context manager call (sitemap discovery) returns sparse list
        instance.aseed_urls = AsyncMock(return_value=sparse_sitemap)
        # Second context manager call (BFS fallback) uses arun
        instance.arun = AsyncMock(return_value=bfs_result)
        MockCrawler.return_value.__aenter__.return_value = instance

        req = MapRequest(url="https://example.com", max_pages=50)
        resp = await map_urls(req)

    assert resp.success is True
    assert resp.total >= 1
    assert resp.start_url == "https://example.com"


# ── aseed_urls dict normalisation ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_map_normalises_dict_urls_from_aseed_urls():
    """aseed_urls returns dicts on some domains — normalise to plain strings."""
    dict_urls = [
        {"url": "https://shopify.com/", "title": "Home"},
        {"url": "https://shopify.com/about", "title": "About"},
        {"url": "https://shopify.com/investors", "title": "Investors"},
        {"url": "https://shopify.com/careers", "title": "Careers"},
        {"url": "https://shopify.com/blog", "title": "Blog"},
        {"url": "https://shopify.com/news", "title": "News"},
    ]

    with patch("scout.core.modes.map.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.aseed_urls = AsyncMock(return_value=dict_urls)
        MockCrawler.return_value.__aenter__.return_value = instance

        req = MapRequest(url="https://shopify.com", max_pages=50)
        resp = await map_urls(req)

    assert resp.success is True
    assert resp.total == 6
    assert all(isinstance(u, str) for u in resp.urls)
    assert "https://shopify.com/" in resp.urls
    assert "https://shopify.com/investors" in resp.urls


@pytest.mark.asyncio
async def test_map_normalises_mixed_url_list():
    """aseed_urls may return a mix of strings and dicts — both are normalised."""
    mixed_urls = [
        "https://example.com/",
        {"url": "https://example.com/about", "title": "About"},
        "https://example.com/contact",
        {"url": "https://example.com/blog"},
        "https://example.com/careers",
        {"url": "https://example.com/investors"},
    ]

    with patch("scout.core.modes.map.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.aseed_urls = AsyncMock(return_value=mixed_urls)
        MockCrawler.return_value.__aenter__.return_value = instance

        req = MapRequest(url="https://example.com", max_pages=50)
        resp = await map_urls(req)

    assert resp.success is True
    assert resp.total == 6
    assert all(isinstance(u, str) for u in resp.urls)


# ── Exception path ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_map_handles_exception_gracefully():
    """Any exception → success=False, empty urls, error message populated."""
    with patch("scout.core.modes.map.AsyncWebCrawler") as MockCrawler:
        MockCrawler.return_value.__aenter__.side_effect = RuntimeError("network timeout")

        req = MapRequest(url="https://example.com")
        resp = await map_urls(req)

    assert resp.success is False
    assert resp.urls == []
    assert resp.total == 0
    assert "network timeout" in resp.error
