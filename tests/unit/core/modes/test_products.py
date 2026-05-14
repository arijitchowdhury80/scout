"""Tests for product catalog crawling mode."""

# Scenario list:
# - mapped category/product URLs produce Algolia records and artifacts
# - missing site/start_url returns a typed failure response
# - category pages can be scraped to discover product links before product scrape
# - explicit category start URLs are scraped before broad mapping
# - blocked product pages keep category-page fallback records and report blocked evidence
# - browser fallback is not used when regular product scrape succeeds
# - browser fallback retries only after a regular product scrape is blocked

from unittest.mock import AsyncMock, patch

import pytest

from scout.core.modes.products import products
from scout.core.types import (
    MapResponse,
    ProductCrawlRequest,
    ScrapeResponse,
    ScoutFormats,
    ScoutMetadata,
)


def _meta(url: str, title: str = "") -> ScoutMetadata:
    return ScoutMetadata(url=url, crawled_at="2026-05-13T00:00:00Z", title=title)


@pytest.mark.asyncio
async def test_products_maps_extracts_records_and_writes_artifacts(tmp_path) -> None:
    product_url = "https://shop.example.com/collections/men-shirts/products/oxford"
    raw_html = """
    <script type="application/ld+json">
    {"@type":"Product","name":"Oxford Shirt","brand":"Example","sku":"OX-1",
     "image":"https://shop.example.com/oxford.jpg",
     "offers":{"price":"79.50","priceCurrency":"USD"}}
    </script>
    """
    map_response = MapResponse(
        success=True,
        start_url="https://shop.example.com",
        urls=[
            "https://shop.example.com/collections/men-shirts",
            product_url,
        ],
        total=2,
        duration_ms=10,
    )
    scrape_response = ScrapeResponse(
        success=True,
        url=product_url,
        markdown="# Oxford Shirt",
        raw_html=raw_html,
        metadata=_meta(product_url, "Oxford Shirt"),
        duration_ms=20,
    )

    with patch(
        "scout.core.modes.products.map_urls", new_callable=AsyncMock, return_value=map_response
    ):
        with patch(
            "scout.core.modes.products.scrape", new_callable=AsyncMock, return_value=scrape_response
        ) as mock_scrape:
            req = ProductCrawlRequest(
                query="men shirts",
                site="shop.example.com",
                limit_per_category=10,
                output_dir=str(tmp_path),
                persist=True,
            )
            resp = await products(req)

    assert resp.success is True
    assert resp.total_records == 1
    assert resp.records[0].name == "Oxford Shirt"
    assert resp.records[0].price == 79.5
    assert resp.output_dir == str(tmp_path)
    assert resp.files.products_json.endswith("algolia/products.json")
    mock_scrape.assert_awaited_once()
    scrape_req = mock_scrape.await_args.args[0]
    assert ScoutFormats.RAW_HTML in scrape_req.formats


@pytest.mark.asyncio
async def test_products_returns_error_when_no_site_or_start_url() -> None:
    resp = await products(ProductCrawlRequest(query="men shirts"))

    assert resp.success is False
    assert "site or start_url" in resp.error


@pytest.mark.asyncio
async def test_products_discovers_product_links_from_category_pages(tmp_path) -> None:
    category_url = "https://www.lacoste.com/us/lacoste/men/clothing/polos"
    product_url = f"{category_url}/L1212-51.html?color=001"
    map_response = MapResponse(
        success=True,
        start_url="https://www.lacoste.com/us",
        urls=[category_url],
        total=1,
        duration_ms=10,
    )
    category_response = ScrapeResponse(
        success=True,
        url=category_url,
        markdown="# Polos",
        links=[product_url],
        metadata=_meta(category_url, "Men's Polos"),
        duration_ms=20,
    )
    product_response = ScrapeResponse(
        success=True,
        url=product_url,
        markdown="# Original Polo",
        raw_html='<script type="application/ld+json">{"@type":"Product","name":"Original Polo"}</script>',
        metadata=_meta(product_url, "Original Polo"),
        duration_ms=20,
    )

    with patch(
        "scout.core.modes.products.map_urls", new_callable=AsyncMock, return_value=map_response
    ):
        with patch(
            "scout.core.modes.products.scrape",
            new_callable=AsyncMock,
            side_effect=[category_response, product_response],
        ):
            req = ProductCrawlRequest(
                query="men polos",
                start_url="https://www.lacoste.com/us",
                limit_per_category=2,
                output_dir=str(tmp_path),
                persist=True,
            )
            resp = await products(req)

    assert resp.success is True
    assert resp.total_records == 1
    assert resp.records[0].url == product_url
    assert resp.records[0].name == "Original Polo"


@pytest.mark.asyncio
async def test_products_scrapes_explicit_category_before_mapping(tmp_path) -> None:
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
    product_response = ScrapeResponse(
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
            side_effect=[category_response, product_response],
        ):
            req = ProductCrawlRequest(
                query="men polos",
                start_url=category_url,
                output_dir=str(tmp_path),
                persist=True,
            )
            resp = await products(req)

    assert resp.success is True
    assert resp.total_records == 1
    mock_map.assert_not_awaited()


@pytest.mark.asyncio
async def test_products_skips_blocked_product_pages(tmp_path) -> None:
    category_url = "https://www.esteelauder.com/skin-care"
    product_url = "https://www.esteelauder.com/product/681/12345/advanced-night-repair-serum"
    category_html = """
    <article class="product-grid__item">
         <a class="product-tile__link"
         href="https://www.esteelauder.com/product/681/12345/advanced-night-repair-serum">
        <img alt="Advanced Night Repair Serum" src="/media/anr.jpg">
        <span class="product-name">Advanced Night Repair Serum</span>
        <span class="price">$85.00</span>
      </a>
    </article>
    """
    category_response = ScrapeResponse(
        success=True,
        url=category_url,
        markdown="# Skin Care",
        raw_html=category_html,
        links=[product_url],
        metadata=_meta(category_url, "Skin Care"),
        duration_ms=20,
    )
    blocked_response = ScrapeResponse(
        success=True,
        url=product_url,
        markdown="Powered and protected by",
        raw_html="<html><title>Access Denied</title></html>",
        metadata=_meta(product_url, "Access Denied"),
        duration_ms=20,
    )

    with patch("scout.core.modes.products.map_urls", new_callable=AsyncMock) as mock_map:
        with patch(
            "scout.core.modes.products.scrape",
            new_callable=AsyncMock,
            side_effect=[category_response, blocked_response],
        ):
            req = ProductCrawlRequest(
                query="skin care",
                start_url=category_url,
                output_dir=str(tmp_path),
                persist=True,
                browser_fallback=False,
            )
            resp = await products(req)

    assert resp.success is True
    assert resp.total_records == 1
    assert resp.records[0].name == "Advanced Night Repair Serum"
    assert resp.records[0].source.extractor == "listing"
    assert resp.records[0].completeness_score > 0
    assert resp.total_blocked_pages == 1
    assert resp.blocked_pages[0].url == product_url
    mock_map.assert_not_awaited()


@pytest.mark.asyncio
async def test_products_does_not_use_browser_fallback_when_regular_scrape_succeeds(
    tmp_path,
) -> None:
    product_url = "https://shop.example.com/products/serum"
    raw_html = """
    <script type="application/ld+json">
    {"@type":"Product","name":"Serum","brand":"Example"}
    </script>
    """
    map_response = MapResponse(
        success=True,
        start_url="https://shop.example.com",
        urls=["https://shop.example.com/collections/skin-care", product_url],
        total=2,
        duration_ms=10,
    )
    product_response = ScrapeResponse(
        success=True,
        url=product_url,
        markdown="# Serum",
        raw_html=raw_html,
        metadata=_meta(product_url, "Serum"),
        duration_ms=20,
    )

    with patch(
        "scout.core.modes.products.map_urls", new_callable=AsyncMock, return_value=map_response
    ):
        with patch(
            "scout.core.modes.products.scrape",
            new_callable=AsyncMock,
            return_value=product_response,
        ) as mock_scrape:
            resp = await products(
                ProductCrawlRequest(
                    query="skin care",
                    site="shop.example.com",
                    output_dir=str(tmp_path),
                    browser_fallback=True,
                )
            )

    assert resp.success is True
    assert resp.total_records == 1
    assert mock_scrape.await_count == 1
    assert mock_scrape.await_args_list[0].args[0].headless is True


@pytest.mark.asyncio
async def test_products_uses_browser_fallback_only_after_blocked_regular_scrape(tmp_path) -> None:
    product_url = "https://shop.example.com/products/serum"
    map_response = MapResponse(
        success=True,
        start_url="https://shop.example.com",
        urls=["https://shop.example.com/collections/skin-care", product_url],
        total=2,
        duration_ms=10,
    )
    blocked_response = ScrapeResponse(
        success=True,
        url=product_url,
        markdown="Access Denied",
        raw_html="<html>Access Denied</html>",
        metadata=_meta(product_url, "Access Denied"),
        duration_ms=20,
    )
    browser_response = ScrapeResponse(
        success=True,
        url=product_url,
        markdown="# Serum",
        raw_html='<script type="application/ld+json">{"@type":"Product","name":"Serum"}</script>',
        metadata=_meta(product_url, "Serum"),
        duration_ms=20,
    )

    with patch(
        "scout.core.modes.products.map_urls", new_callable=AsyncMock, return_value=map_response
    ):
        with patch(
            "scout.core.modes.products.scrape",
            new_callable=AsyncMock,
            side_effect=[blocked_response, browser_response],
        ) as mock_scrape:
            resp = await products(
                ProductCrawlRequest(
                    query="skin care",
                    site="shop.example.com",
                    output_dir=str(tmp_path),
                    browser_fallback=True,
                )
            )

    assert resp.success is True
    assert resp.total_records == 1
    assert resp.records[0].name == "Serum"
    assert resp.records[0].source.extractor == "jsonld_browser_fallback"
    assert resp.total_blocked_pages == 1
    assert resp.blocked_pages[0].fallback_used is True
    regular_req = mock_scrape.await_args_list[0].args[0]
    browser_req = mock_scrape.await_args_list[1].args[0]
    assert regular_req.headless is True
    assert browser_req.headless is False
    assert browser_req.stealth is True
