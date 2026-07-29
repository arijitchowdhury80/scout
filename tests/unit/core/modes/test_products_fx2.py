"""FX-2 regression test — success-but-empty-products must trigger the
browser fallback.

Root-caused from the 2026-07-27 e2e re-run: lacoste.com's primary product
fetch returns `success=True` (the render worked) but the page contains no
schema.org Product JSON-LD, so `extract_product_jsonld` returns None. The
FX-1b fallback trigger only fired on `success=False`, so this
success-but-empty case fell straight through to a title-only placeholder
record and the aggregate crawl reported `fallback_attempted: false`,
reason `no_product_records` — no fallback ever ran even though one was
available.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from scout.core.modes.products import products
from scout.core.types import (
    ProductCrawlRequest,
    ScrapeResponse,
    ScoutMetadata,
)


def _meta(url: str, title: str = "") -> ScoutMetadata:
    return ScoutMetadata(url=url, crawled_at="2026-07-27T00:00:00Z", title=title)


@pytest.mark.asyncio
async def test_success_with_zero_products_engages_browser_fallback_and_recovers(
    tmp_path,
) -> None:
    """Primary fetch succeeds but extracts no product JSON-LD (the lacoste
    repro). The browser fallback must still be invoked and, since it
    recovers real content here, a record must be produced."""
    category_url = "https://www.lacoste.com/us/lacoste/men/clothing/polos"
    product_url = f"{category_url}/L1212-51.html?color=001"

    category_response = ScrapeResponse(
        success=True,
        url=category_url,
        markdown="# Polos",
        links=[product_url],
        metadata=_meta(category_url, "Men's Polos"),
        duration_ms=20,
    )
    # Fetch SUCCEEDS but the page has no Product JSON-LD at all.
    empty_primary = ScrapeResponse(
        success=True,
        url=product_url,
        markdown="# Original Polo",
        raw_html="<html><body>Original Polo</body></html>",
        metadata=_meta(product_url, "Original Polo"),
        duration_ms=20,
    )
    browser_fallback_response = ScrapeResponse(
        success=True,
        url=product_url,
        markdown="# Original Polo",
        raw_html='<script type="application/ld+json">{"@type":"Product","name":"Original Polo"}</script>',
        metadata=_meta(product_url, "Original Polo"),
        duration_ms=20,
    )

    with patch("scout.core.modes.products.map_urls", new_callable=AsyncMock) as mock_map:
        with patch(
            "scout.core.modes.products.scrape",
            new_callable=AsyncMock,
            side_effect=[category_response, empty_primary, browser_fallback_response],
        ) as mock_scrape:
            req = ProductCrawlRequest(
                query="men polos",
                start_url=category_url,
                limit_per_category=2,
                output_dir=str(tmp_path),
                persist=True,
                browser_fallback=True,
            )
            resp = await products(req)

    assert resp.success is True
    mock_map.assert_not_awaited()
    # Fallback must have actually been called (3rd scrape call = fallback retry).
    assert mock_scrape.await_count == 3
    fallback_req = mock_scrape.await_args_list[2].args[0]
    assert fallback_req.headless is True

    assert resp.total_records == 1
    assert resp.records[0].name == "Original Polo"
    assert resp.total_blocked_pages == 1
    assert resp.blocked_pages[0].reason == "no_product_records"
    assert resp.blocked_pages[0].fallback_attempted is True
    assert resp.blocked_pages[0].fallback_used is True


@pytest.mark.asyncio
async def test_success_with_zero_products_and_failed_fallback_reports_honest_empty(
    tmp_path,
) -> None:
    """When the primary fetch succeeds with zero products AND the fallback
    also finds nothing, report an honest blocked reason instead of
    fabricating a title-only placeholder record."""
    category_url = "https://www.lacoste.com/us/lacoste/men/clothing/polos"
    product_url = f"{category_url}/L1212-51.html?color=001"

    category_response = ScrapeResponse(
        success=True,
        url=category_url,
        markdown="# Polos",
        links=[product_url],
        metadata=_meta(category_url, "Men's Polos"),
        duration_ms=20,
    )
    empty_primary = ScrapeResponse(
        success=True,
        url=product_url,
        markdown="# Original Polo",
        raw_html="<html><body>Original Polo</body></html>",
        metadata=_meta(product_url, "Original Polo"),
        duration_ms=20,
    )
    empty_fallback = ScrapeResponse(
        success=True,
        url=product_url,
        markdown="# Original Polo",
        raw_html="<html><body>Original Polo, still no JSON-LD</body></html>",
        metadata=_meta(product_url, "Original Polo"),
        duration_ms=20,
    )

    with patch("scout.core.modes.products.map_urls", new_callable=AsyncMock) as mock_map:
        with patch(
            "scout.core.modes.products.scrape",
            new_callable=AsyncMock,
            side_effect=[category_response, empty_primary, empty_fallback],
        ) as mock_scrape:
            req = ProductCrawlRequest(
                query="men polos",
                start_url=category_url,
                limit_per_category=2,
                output_dir=str(tmp_path),
                persist=True,
                browser_fallback=True,
            )
            resp = await products(req)

    assert resp.success is True
    assert mock_scrape.await_count == 3  # fallback WAS attempted
    assert resp.total_records == 0
    assert resp.total_blocked_pages == 1
    assert resp.blocked_pages[0].reason == "no_product_records"
    assert resp.blocked_pages[0].fallback_attempted is True
    assert resp.blocked_pages[0].fallback_used is False
    mock_map.assert_not_awaited()
