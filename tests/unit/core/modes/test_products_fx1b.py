"""FX-1b regression test — products browser fallback must actually engage.

Root-caused from docs/test-results-2026-07-26/FAILURE-REPORT.md (F1b/F3) and
FIX-PLAN.md FX-1b: lacoste.com / eyebuydirect.com primary scrapes come back
success=False (empty render), and the old code path did `continue` on a
failed primary scrape WITHOUT ever calling the browser fallback — so
blocked_pages ended up reporting `fallback_attempted=True` (an artifact of
just echoing the config flag) while `fallback_used` stayed False, because no
fallback ever ran.
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
async def test_failed_primary_fetch_engages_browser_fallback_and_recovers(tmp_path) -> None:
    """Primary scrape returns success=False (the exact lacoste/eyebuydirect repro).

    The browser fallback must actually be invoked (fallback_used=True) and,
    since it recovers real content here, a record must be produced.
    """
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
    failed_primary = ScrapeResponse(
        success=False,
        url=product_url,
        markdown="",
        error="",
        status_code=None,
        metadata=_meta(product_url),
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
            side_effect=[category_response, failed_primary, browser_fallback_response],
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
    # FX-1: hosted container has no X server — fallback must run headless
    # by default (a headed launch crashes with "Missing X server or
    # $DISPLAY", the eyebuydirect repro).
    assert fallback_req.headless is True

    assert resp.total_records == 1
    assert resp.records[0].name == "Original Polo"
    assert resp.total_blocked_pages == 1
    assert resp.blocked_pages[0].fallback_attempted is True
    assert resp.blocked_pages[0].fallback_used is True  # was falsely False before the fix


@pytest.mark.asyncio
async def test_failed_primary_fetch_with_fallback_still_failing_reports_honest_blocked(
    tmp_path,
) -> None:
    """When even the fallback can't recover content, report an honest blocked reason
    instead of a silent empty result."""
    category_url = "https://www.eyebuydirect.com/us/eyebuydirect/eyeglasses"
    product_url = f"{category_url}/EBD-4021.html?color=001"

    category_response = ScrapeResponse(
        success=True,
        url=category_url,
        markdown="# Eyeglasses",
        links=[product_url],
        metadata=_meta(category_url, "Eyeglasses"),
        duration_ms=20,
    )
    failed_primary = ScrapeResponse(
        success=False,
        url=product_url,
        markdown="",
        error="",
        status_code=None,
        metadata=_meta(product_url),
        duration_ms=20,
    )
    failed_fallback = ScrapeResponse(
        success=False,
        url=product_url,
        markdown="",
        error="net::ERR_HTTP2_PROTOCOL_ERROR",
        status_code=None,
        metadata=_meta(product_url),
        duration_ms=20,
    )

    with patch("scout.core.modes.products.map_urls", new_callable=AsyncMock) as mock_map:
        with patch(
            "scout.core.modes.products.scrape",
            new_callable=AsyncMock,
            side_effect=[category_response, failed_primary, failed_fallback],
        ) as mock_scrape:
            req = ProductCrawlRequest(
                query="eyeglasses",
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
    assert resp.blocked_pages[0].fallback_attempted is True
    assert resp.blocked_pages[0].fallback_used is False
    assert resp.blocked_pages[0].reason  # honest reason, not blank
    mock_map.assert_not_awaited()
