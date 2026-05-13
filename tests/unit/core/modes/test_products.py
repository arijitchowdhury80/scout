"""Tests for product catalog crawling mode."""

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
