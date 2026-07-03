"""Tests for the anonymous hosted Scout playground."""

from __future__ import annotations

from fastapi.testclient import TestClient

from scout.api.deps import get_crawler, get_playground_admission_controller
from scout.api.main import app
from scout.api.routers import playground as playground_router
from scout.core.platform.admission import AdmissionController
from scout.core.types import (
    AlgoliaProductRecord,
    BlockedPage,
    CrawlPage,
    CrawlResponse,
    ExtractResponse,
    MapResponse,
    ProductArtifactFiles,
    ProductCrawlResponse,
    ProductSource,
    ScoutMetadata,
    ScrapeResponse,
    ScreenshotResponse,
)


ALL_PLAYGROUND_CAPABILITIES = {
    "scrape",
    "crawl",
    "map",
    "screenshot",
    "products",
    "company",
    "investor",
    "careers",
    "news",
    "social",
    "locations",
}
INTERNAL_OR_UTILITY_WORKFLOWS = {
    "extract",
    "jobs",
    "prism",
    "research",
    "docs",
    "website-quality",
}


class _FakePlaygroundCrawler:
    def __init__(self) -> None:
        self.product_request = None
        self.crawl_request = None
        self.scrape_request = None
        self.map_request = None
        self.extract_request = None
        self.screenshot_request = None

    async def scrape(self, req):
        self.scrape_request = req
        markdown = (
            "# Demo Company\n\n"
            "Demo Company builds useful web tools. Jane Doe, Chief Executive Officer.\n"
            "Careers Engineering Sales. Latest news and blog updates.\n"
            "[LinkedIn](https://www.linkedin.com/company/demo-company)\n"
            "Address: 123 Market Street, San Francisco, CA 94105\n"
        )
        return ScrapeResponse(
            success=True,
            url=req.url,
            markdown=markdown,
            raw_markdown=markdown,
            clean_markdown=markdown,
            raw_html=(
                "<html><head><title>Demo Company</title>"
                "<meta name='viewport' content='width=device-width'>"
                "<meta name='description' content='Demo company'>"
                "<meta property='og:title' content='Demo Company'>"
                "<script type='application/ld+json'>{}</script></head>"
                "<body><main><h1>Demo Company</h1><img alt='Demo' src='demo.png'>"
                "<a href='/about'>About</a><a href='/careers'>Careers</a></main></body></html>"
            ),
            links=[
                "https://www.linkedin.com/company/demo-company",
                "https://example.com/about",
                "https://example.com/careers",
                "https://example.com/news",
            ],
            metadata=ScoutMetadata(
                url=req.url,
                crawled_at="2026-06-30T00:00:00Z",
                title="Demo Company",
                word_count=32,
            ),
            final_url=req.url,
            fetched_at="2026-06-30T00:00:00Z",
            provider="fake",
            content_hash="abc123",
            quality_score=0.95,
            quality_reasons=["title_present", "not_blocked"],
            duration_ms=10,
        )

    async def map_urls(self, req):
        self.map_request = req
        return MapResponse(
            success=True,
            start_url=req.url,
            urls=[req.url, f"{req.url.rstrip('/')}/about", f"{req.url.rstrip('/')}/careers"],
            total=3,
            duration_ms=7,
        )

    async def extract(self, req):
        self.extract_request = req
        return ExtractResponse(
            success=True,
            url=req.url,
            data={"title": "Demo Company", "summary": "Useful extracted data"},
            markdown="# Demo Company\n\nUseful extracted data.",
            metadata=ScoutMetadata(
                url=req.url,
                crawled_at="2026-06-30T00:00:00Z",
                title="Demo Company",
                word_count=4,
            ),
            duration_ms=9,
        )

    async def screenshot(self, req):
        self.screenshot_request = req
        return ScreenshotResponse(
            success=True,
            url=req.url,
            screenshot_base64="iVBORw0KGgo=",
            width=req.viewport_width,
            height=req.viewport_height,
            duration_ms=11,
        )

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


def test_playground_accepts_scheme_less_public_urls() -> None:
    crawler = _FakePlaygroundCrawler()
    app.dependency_overrides[get_crawler] = lambda: crawler
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/playground/run",
            json={
                "workflow": "scrape",
                "url": "example.com",
                "max_items": 1,
                "output_format": "json",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["url"] == "https://example.com"
    assert payload["records"][0]["url"] == "https://example.com"
    assert crawler.scrape_request.url == "https://example.com"


def test_playground_rejects_when_demo_capacity_is_full_without_running_crawler() -> None:
    crawler = _FakePlaygroundCrawler()
    admission = AdmissionController(max_active=0, retry_after_seconds=4)
    app.dependency_overrides[get_crawler] = lambda: crawler
    app.dependency_overrides[get_playground_admission_controller] = lambda: admission
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/playground/run",
            json={
                "workflow": "scrape",
                "url": "example.com",
                "max_items": 1,
                "output_format": "json",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 429
    assert resp.json()["detail"] == "Playground capacity is full; retry shortly."
    assert resp.headers["retry-after"] == "4"
    assert crawler.scrape_request is None


def test_playground_crawl_demo_is_public_limited_and_downloadable() -> None:
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
    assert payload["workflow"] == "crawl"
    assert payload["limits"]["max_pages"] == 5
    assert payload["summary"]["page_count"] == 1
    assert payload["records"][0]["markdown"] == "# Demo page\n\nUseful content."
    assert "# Demo page" in payload["downloads"]["markdown"]
    assert "Demo page" in payload["downloads"]["json"]
    assert crawler.crawl_request.max_pages == 5
    assert crawler.crawl_request.max_depth == 1
    assert crawler.crawl_request.include_external is False
    assert crawler.crawl_request.timeout_ms <= 30_000


def test_playground_capabilities_endpoint_lists_public_demo_features_only() -> None:
    client = TestClient(app)

    resp = client.get("/v1/playground/capabilities")

    assert resp.status_code == 200
    payload = resp.json()
    capability_names = {capability["name"] for capability in payload["capabilities"]}
    assert capability_names == ALL_PLAYGROUND_CAPABILITIES
    assert capability_names.isdisjoint(INTERNAL_OR_UTILITY_WORKFLOWS)
    assert payload["limits"]["max_products"] == 10
    assert payload["limits"]["max_pages"] == 5
    assert payload["limits"]["max_records"] == 10


def test_playground_rate_limit_allows_one_full_capability_tour() -> None:
    """The public playground promises users can try every listed capability."""
    crawler = _FakePlaygroundCrawler()
    client_ip = "198.51.100.88"
    playground_router._RATE_BUCKETS.pop(client_ip, None)
    app.dependency_overrides[get_crawler] = lambda: crawler
    try:
        client = TestClient(app)
        capabilities_resp = client.get("/v1/playground/capabilities")
        assert capabilities_resp.status_code == 200
        capabilities = [
            capability["name"] for capability in capabilities_resp.json()["capabilities"]
        ]
        assert capabilities_resp.json()["limits"]["requests_per_hour"] >= len(capabilities)

        statuses = []
        for capability in capabilities:
            resp = client.post(
                "/v1/playground/run",
                headers={"X-Forwarded-For": client_ip},
                json={
                    "workflow": capability,
                    "url": "https://example.com",
                    "query": "Demo Company",
                    "max_items": 99,
                    "output_format": "json",
                },
            )
            statuses.append((capability, resp.status_code))
    finally:
        app.dependency_overrides.clear()
        playground_router._RATE_BUCKETS.pop(client_ip, None)

    assert statuses == [(capability, 200) for capability in capabilities]


def test_playground_runs_all_scout_capabilities_with_public_caps() -> None:
    for index, capability in enumerate(sorted(ALL_PLAYGROUND_CAPABILITIES), start=1):
        crawler = _FakePlaygroundCrawler()
        app.dependency_overrides[get_crawler] = lambda: crawler
        try:
            client = TestClient(app)
            resp = client.post(
                "/v1/playground/run",
                headers={"X-Forwarded-For": f"198.51.100.{index}"},
                json={
                    "workflow": capability,
                    "url": "https://example.com",
                    "query": "Demo Company",
                    "max_items": 99,
                    "output_format": "json",
                },
            )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200, capability
        payload = resp.json()
        assert payload["workflow"] == capability
        assert payload["success"] is True
        assert payload["summary"]["capped"] is True
        assert payload["summary"]["record_count"] >= 1
        assert payload["downloads"]["json"]
        assert payload["downloads"]["markdown"]
        assert payload["download_filenames"]["json"] == f"scout-playground-{capability}.json"


def test_playground_rejects_internal_utility_workflows() -> None:
    crawler = _FakePlaygroundCrawler()
    app.dependency_overrides[get_crawler] = lambda: crawler
    try:
        client = TestClient(app)
        for workflow in sorted(INTERNAL_OR_UTILITY_WORKFLOWS):
            resp = client.post(
                "/v1/playground/run",
                headers={"X-Forwarded-For": f"198.51.101.{len(workflow)}"},
                json={
                    "workflow": workflow,
                    "url": "https://example.com",
                    "query": "Demo Company",
                    "max_items": 99,
                    "output_format": "json",
                },
            )
            assert resp.status_code == 400, workflow
            assert "Unsupported playground workflow" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_playground_rejects_private_or_local_urls_without_running() -> None:
    crawler = _FakePlaygroundCrawler()
    app.dependency_overrides[get_crawler] = lambda: crawler
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/playground/run",
            headers={"X-Forwarded-For": "198.51.100.200"},
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
