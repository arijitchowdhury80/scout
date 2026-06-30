"""Tests for the anonymous hosted Scout playground."""

from __future__ import annotations

from fastapi.testclient import TestClient

from scout.api.deps import get_crawler
from scout.api.main import app
from scout.core.types import (
    AlgoliaProductRecord,
    BlockedPage,
    CrawlPage,
    CrawlResponse,
    ProductArtifactFiles,
    ProductCrawlResponse,
    ProductSource,
    ScoutMetadata,
)


class _FakePlaygroundCrawler:
    def __init__(self) -> None:
        self.product_request = None
        self.crawl_request = None

    async def products(self, req):
        self.product_request = req
        return ProductCrawlResponse(
            success=True,
            query=req.query,
            site=req.site,
            start_url=req.start_url,
            output_dir="",
            records=[
                AlgoliaProductRecord(
                    objectID="demo-product-1",
                    name="Demo Serum",
                    url="https://shop.example.com/products/demo-serum",
                    brand="Demo",
                    price=42.0,
                    currency="USD",
                    source=ProductSource(
                        url="https://shop.example.com/category/skincare",
                        extractor="listing",
                    ),
                    citations=[
                        {
                            "source_url": "https://shop.example.com/category/skincare",
                            "field": "name",
                            "snippet": "Demo Serum",
                            "confidence": 0.9,
                        }
                    ],
                    completeness_score=0.75,
                )
            ],
            total_records=1,
            categories=["Skincare"],
            blocked_pages=[
                BlockedPage(
                    url="https://shop.example.com/products/detail",
                    reason="detail page blocked",
                )
            ],
            total_blocked_pages=1,
            files=ProductArtifactFiles(),
            duration_ms=12,
        )

    async def crawl(self, req):
        self.crawl_request = req
        return CrawlResponse(
            success=True,
            start_url=req.url,
            pages=[
                CrawlPage(
                    url=req.url,
                    markdown="# Demo page\n\nUseful content.",
                    metadata=ScoutMetadata(
                        url=req.url,
                        crawled_at="2026-06-30T00:00:00Z",
                        title="Demo page",
                        word_count=3,
                    ),
                    success=True,
                )
            ],
            total_pages=1,
            duration_ms=8,
        )


def test_playground_product_demo_is_public_limited_and_downloadable() -> None:
    crawler = _FakePlaygroundCrawler()
    app.dependency_overrides[get_crawler] = lambda: crawler
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/playground/run",
            json={
                "workflow": "products",
                "url": "https://shop.example.com/category/skincare",
                "max_items": 50,
                "output_format": "json",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["workflow"] == "products"
    assert payload["limits"]["max_products"] == 10
    assert payload["summary"]["record_count"] == 1
    assert payload["summary"]["blocked_count"] == 1
    assert payload["records"][0]["name"] == "Demo Serum"
    assert "Demo Serum" in payload["downloads"]["json"]
    assert "Demo Serum" in payload["downloads"]["markdown"]
    assert payload["download_filenames"]["json"] == "scout-playground-products.json"
    assert crawler.product_request.max_products == 10
    assert crawler.product_request.max_categories == 1
    assert crawler.product_request.limit_per_category == 10
    assert crawler.product_request.persist is False
    assert crawler.product_request.timeout_ms <= 30_000


def test_playground_website_demo_is_public_limited_and_downloadable() -> None:
    crawler = _FakePlaygroundCrawler()
    app.dependency_overrides[get_crawler] = lambda: crawler
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/playground/run",
            json={
                "workflow": "website",
                "url": "https://example.com",
                "max_items": 99,
                "output_format": "markdown",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["workflow"] == "website"
    assert payload["limits"]["max_pages"] == 5
    assert payload["summary"]["page_count"] == 1
    assert payload["records"][0]["markdown"] == "# Demo page\n\nUseful content."
    assert "# Demo page" in payload["downloads"]["markdown"]
    assert "Demo page" in payload["downloads"]["json"]
    assert crawler.crawl_request.max_pages == 5
    assert crawler.crawl_request.max_depth == 1
    assert crawler.crawl_request.include_external is False
    assert crawler.crawl_request.timeout_ms <= 30_000


def test_playground_rejects_private_or_local_urls_without_running() -> None:
    crawler = _FakePlaygroundCrawler()
    app.dependency_overrides[get_crawler] = lambda: crawler
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/playground/run",
            json={
                "workflow": "website",
                "url": "http://127.0.0.1:8421/health",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert "unsafe" in resp.json()["detail"].lower()
    assert crawler.crawl_request is None
    assert crawler.product_request is None
