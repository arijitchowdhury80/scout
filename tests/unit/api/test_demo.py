"""Tests for the anonymous PLG homepage demo endpoint (/v1/demo/*).

Spec: docs/product/plg-playground-ux.md — anonymous "taste" tier.
- POST /v1/demo/scrape, /v1/demo/map, /v1/demo/crawl, /v1/demo/products — no auth.
- Scaled-down only (never full crawl/products/company/screenshot at full power):
  crawl is hard-capped at max_pages=3, http-first only; products is hard-capped
  at 5 records via single-page http-first extraction (no browser fallback).
- All four endpoints share ONE per-IP daily quota pool (5 runs/IP/day) plus a
  shared global daily ceiling.
- Preview output: truncated, with an upsell flag/message.
- Blocks unsafe/private targets via the existing hosted URL-safety check.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from scout.api.routers import demo as demo_router
from scout.core.types import (
    CrawlPage,
    CrawlResponse,
    MapResponse,
    ScoutFormats,
    ScoutMetadata,
    ScrapeResponse,
)


def _build_demo_app() -> FastAPI:
    """Build a minimal app with only the demo router mounted.

    scout/api/main.py is intentionally not touched by this task (a later step
    wires the router + the AuthMiddleware public-path whitelist there). This
    harness unit-tests the router's own behavior in isolation — no auth
    middleware, no other routers — matching the "no auth required" spec.
    """
    app = FastAPI()
    app.include_router(demo_router.router)
    return app


_PRODUCT_LISTING_HTML = """
<html><body>
<a href="/products/widget-1" class="product-card">
  <img src="/img/widget-1.jpg" />
  <span class="product-name">Widget One</span>
  <span class="price">$19.99</span>
</a>
<a href="/products/widget-2" class="product-card">
  <img src="/img/widget-2.jpg" />
  <span class="product-name">Widget Two</span>
  <span class="price">$29.99</span>
</a>
<a href="/products/widget-3" class="product-card">
  <img src="/img/widget-3.jpg" />
  <span class="product-name">Widget Three</span>
  <span class="price">$39.99</span>
</a>
<a href="/products/widget-4" class="product-card">
  <img src="/img/widget-4.jpg" />
  <span class="product-name">Widget Four</span>
  <span class="price">$49.99</span>
</a>
<a href="/products/widget-5" class="product-card">
  <img src="/img/widget-5.jpg" />
  <span class="product-name">Widget Five</span>
  <span class="price">$59.99</span>
</a>
<a href="/products/widget-6" class="product-card">
  <img src="/img/widget-6.jpg" />
  <span class="product-name">Widget Six</span>
  <span class="price">$69.99</span>
</a>
</body></html>
"""


class _FakeDemoCrawler:
    def __init__(self, *, product_html: str = _PRODUCT_LISTING_HTML) -> None:
        self.scrape_request = None
        self.map_request = None
        self.crawl_request = None
        self._product_html = product_html

    async def scrape(self, req):
        self.scrape_request = req
        markdown = "# Demo Company\n\n" + ("Useful evidence-grade content. " * 200)
        wants_html = ScoutFormats.RAW_HTML in req.formats
        raw_html = self._product_html if wants_html else ""
        links = [f"/products/widget-{i}" for i in range(1, 7)] if wants_html else []
        return ScrapeResponse(
            success=True,
            url=req.url,
            markdown=markdown,
            raw_markdown=markdown,
            clean_markdown=markdown,
            raw_html=raw_html,
            links=links,
            metadata=ScoutMetadata(
                url=req.url,
                crawled_at="2026-07-06T00:00:00Z",
                title="Demo Company",
                word_count=2000,
            ),
            final_url=req.url,
            fetched_at="2026-07-06T00:00:00Z",
            provider="fake",
            content_hash="abc123",
            quality_score=0.9,
            quality_reasons=["title_present", "not_blocked"],
            duration_ms=10,
        )

    async def map_urls(self, req):
        self.map_request = req
        urls = [f"{req.url.rstrip('/')}/page-{i}" for i in range(50)]
        return MapResponse(
            success=True,
            start_url=req.url,
            urls=urls,
            total=len(urls),
            duration_ms=5,
        )

    async def crawl(self, req):
        self.crawl_request = req
        pages = [
            CrawlPage(
                url=f"{req.url.rstrip('/')}/page-{i}",
                markdown=f"# Page {i}\n\n" + ("Content. " * 50),
                metadata=ScoutMetadata(
                    url=f"{req.url.rstrip('/')}/page-{i}",
                    crawled_at="2026-07-06T00:00:00Z",
                    title=f"Page {i}",
                    word_count=100,
                ),
                success=True,
            )
            for i in range(10)  # crawler would happily return more than the demo cap
        ]
        return CrawlResponse(
            success=True,
            start_url=req.url,
            pages=pages,
            total_pages=len(pages),
            duration_ms=20,
        )


def test_demo_scrape_requires_no_auth_and_returns_preview() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/scrape",
        headers={"X-Forwarded-For": "203.0.113.10"},
        json={"url": "example.com"},
    )
    demo_router.reset_state_for_tests()

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["preview"] is True
    assert "sign up" in payload["upsell_message"].lower()
    assert crawler.scrape_request.url == "https://example.com"
    # No auth header/key was supplied and the request still succeeded.


def test_demo_scrape_truncates_long_markdown() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/scrape",
        headers={"X-Forwarded-For": "203.0.113.11"},
        json={"url": "https://example.com"},
    )
    demo_router.reset_state_for_tests()

    payload = resp.json()
    assert payload["truncated"] is True
    assert len(payload["record"]["markdown"]) <= demo_router.MAX_PREVIEW_CHARS
    assert crawler.scrape_request is not None


def test_demo_map_returns_truncated_url_list_and_evidence() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/map",
        headers={"X-Forwarded-For": "203.0.113.12"},
        json={"url": "https://example.com"},
    )
    demo_router.reset_state_for_tests()

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["preview"] is True
    assert len(payload["record"]["urls"]) <= demo_router.MAX_MAP_URLS
    assert payload["record"]["total_discovered"] == 50
    assert "sign up" in payload["upsell_message"].lower()
    assert payload["evidence"]["source"] == "https://example.com"


def test_demo_evidence_panel_present_on_scrape() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/scrape",
        headers={"X-Forwarded-For": "203.0.113.13"},
        json={"url": "https://example.com"},
    )
    demo_router.reset_state_for_tests()

    payload = resp.json()
    evidence = payload["evidence"]
    assert evidence["source"] == "https://example.com"
    assert evidence["content_hash"] == "abc123"
    assert evidence["verified"] is True


def test_demo_rejects_sixth_run_from_same_ip_in_one_day() -> None:
    crawler = _FakeDemoCrawler()
    client_ip = "203.0.113.20"
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    statuses = []
    for _ in range(6):
        resp = client.post(
            "/v1/demo/scrape",
            headers={"X-Forwarded-For": client_ip},
            json={"url": "https://example.com"},
        )
        statuses.append(resp.status_code)
    demo_router.reset_state_for_tests()

    assert statuses == [200, 200, 200, 200, 200, 429]


def test_demo_per_ip_limit_is_independent_per_client() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    for _ in range(5):
        resp = client.post(
            "/v1/demo/scrape",
            headers={"X-Forwarded-For": "203.0.113.30"},
            json={"url": "https://example.com"},
        )
        assert resp.status_code == 200
    # A different IP should not be blocked by the first IP's usage.
    resp = client.post(
        "/v1/demo/scrape",
        headers={"X-Forwarded-For": "203.0.113.31"},
        json={"url": "https://example.com"},
    )
    demo_router.reset_state_for_tests()

    assert resp.status_code == 200


def test_demo_rejects_request_once_global_daily_ceiling_reached() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    original_ceiling = demo_router.GLOBAL_DAILY_CEILING
    demo_router.GLOBAL_DAILY_CEILING = 2
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    try:
        statuses = []
        for i in range(3):
            resp = client.post(
                "/v1/demo/scrape",
                headers={"X-Forwarded-For": f"203.0.113.{40 + i}"},
                json={"url": "https://example.com"},
            )
            statuses.append(resp.status_code)
    finally:
        demo_router.GLOBAL_DAILY_CEILING = original_ceiling
        demo_router.reset_state_for_tests()

    assert statuses == [200, 200, 429]


def test_demo_rejects_private_or_local_urls_without_running() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/scrape",
        headers={"X-Forwarded-For": "203.0.113.50"},
        json={"url": "http://127.0.0.1:8421/health"},
    )
    demo_router.reset_state_for_tests()

    assert resp.status_code == 403
    assert "unsafe" in resp.json()["detail"].lower()
    assert crawler.scrape_request is None


def test_demo_map_rejects_private_or_local_urls_without_running() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/map",
        headers={"X-Forwarded-For": "203.0.113.51"},
        json={"url": "http://169.254.169.254/latest/meta-data"},
    )
    demo_router.reset_state_for_tests()

    assert resp.status_code == 403
    assert crawler.map_request is None


def test_demo_rejects_disallowed_workflows_via_url_field_only() -> None:
    """The demo router only exposes scrape/map/crawl/products — never company/screenshot."""
    app = _build_demo_app()
    client = TestClient(app)
    for path in ("/v1/demo/company", "/v1/demo/screenshot"):
        resp = client.post(path, json={"url": "https://example.com"})
        assert resp.status_code == 404, path


def test_demo_capacity_full_returns_429_without_running_crawler() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    admission = demo_router.DemoAdmissionController(max_active=0, retry_after_seconds=3)
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    app.dependency_overrides[demo_router.get_demo_admission_controller] = lambda: admission
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/scrape",
        headers={"X-Forwarded-For": "203.0.113.60"},
        json={"url": "https://example.com"},
    )
    demo_router.reset_state_for_tests()

    assert resp.status_code == 429
    assert resp.headers["retry-after"] == "3"
    assert crawler.scrape_request is None


def test_demo_scrape_response_never_includes_screenshot_or_raw_html_fields() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/scrape",
        headers={"X-Forwarded-For": "203.0.113.70"},
        json={"url": "https://example.com"},
    )
    demo_router.reset_state_for_tests()

    record = resp.json()["record"]
    assert "screenshot_base64" not in record
    assert "raw_html" not in record


def test_demo_router_declared_capabilities_are_fast_only() -> None:
    """Documented invariant: demo router exposes only these four scaled-down workflows."""
    assert demo_router.ALLOWED_WORKFLOWS == {"scrape", "map", "crawl", "products"}


# --- POST /v1/demo/crawl ---------------------------------------------------------------


def test_demo_crawl_requires_no_auth_and_returns_preview() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/crawl",
        headers={"X-Forwarded-For": "203.0.113.80"},
        json={"url": "example.com"},
    )
    demo_router.reset_state_for_tests()

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["preview"] is True
    assert "sign up" in payload["upsell_message"].lower()
    assert crawler.crawl_request.url == "https://example.com"


def test_demo_crawl_hard_caps_at_three_pages_http_only() -> None:
    """Even though the fake crawler returns 10 pages, the request must cap max_pages=3
    and the response records list must never exceed 3 — and use_js must be False
    (http-first only, per spec)."""
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/crawl",
        headers={"X-Forwarded-For": "203.0.113.81"},
        json={"url": "https://example.com"},
    )
    demo_router.reset_state_for_tests()

    assert crawler.crawl_request.max_pages == 3
    assert crawler.crawl_request.use_js is False
    payload = resp.json()
    assert len(payload["record"]["pages"]) <= 3


def test_demo_crawl_marks_truncated_when_more_pages_exist() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/crawl",
        headers={"X-Forwarded-For": "203.0.113.82"},
        json={"url": "https://example.com"},
    )
    demo_router.reset_state_for_tests()

    payload = resp.json()
    assert payload["truncated"] is True


def test_demo_crawl_evidence_and_truncated_page_markdown() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/crawl",
        headers={"X-Forwarded-For": "203.0.113.83"},
        json={"url": "https://example.com"},
    )
    demo_router.reset_state_for_tests()

    payload = resp.json()
    assert payload["evidence"]["source"] == "https://example.com"
    for page in payload["record"]["pages"]:
        assert len(page["markdown"]) <= demo_router.MAX_PREVIEW_CHARS


def test_demo_crawl_rejects_private_or_local_urls_without_running() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/crawl",
        headers={"X-Forwarded-For": "203.0.113.84"},
        json={"url": "http://127.0.0.1:8421/health"},
    )
    demo_router.reset_state_for_tests()

    assert resp.status_code == 403
    assert crawler.crawl_request is None


def test_demo_crawl_capacity_full_returns_429_without_running_crawler() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    admission = demo_router.DemoAdmissionController(max_active=0, retry_after_seconds=3)
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    app.dependency_overrides[demo_router.get_demo_admission_controller] = lambda: admission
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/crawl",
        headers={"X-Forwarded-For": "203.0.113.85"},
        json={"url": "https://example.com"},
    )
    demo_router.reset_state_for_tests()

    assert resp.status_code == 429
    assert crawler.crawl_request is None


# --- POST /v1/demo/products -------------------------------------------------------------


def test_demo_products_requires_no_auth_and_returns_preview() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/products",
        headers={"X-Forwarded-For": "203.0.113.90"},
        json={"url": "example.com"},
    )
    demo_router.reset_state_for_tests()

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["preview"] is True
    assert "sign up" in payload["upsell_message"].lower()
    assert crawler.scrape_request.url == "https://example.com"


def test_demo_products_uses_http_first_single_page_scrape() -> None:
    """Products demo must scrape a single page, no browser/use_js, requesting raw_html
    so the listing extractor has anchors + JSON-LD to work with."""
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    client.post(
        "/v1/demo/products",
        headers={"X-Forwarded-For": "203.0.113.91"},
        json={"url": "https://example.com"},
    )
    demo_router.reset_state_for_tests()

    assert crawler.scrape_request.use_js is False
    assert ScoutFormats.RAW_HTML in crawler.scrape_request.formats


def test_demo_products_hard_caps_at_five_records() -> None:
    """Fake page has 6 extractable product cards; response must cap at 5."""
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/products",
        headers={"X-Forwarded-For": "203.0.113.92"},
        json={"url": "https://example.com"},
    )
    demo_router.reset_state_for_tests()

    payload = resp.json()
    assert payload["success"] is True
    records = payload["record"]["records"]
    assert len(records) <= 5
    assert len(records) == 5  # 6 cards on the fake page, capped to 5
    assert payload["truncated"] is True


def test_demo_products_returns_empty_records_when_nothing_extractable_no_fake_data() -> None:
    """If the page has no extractable product-ish markup, return success with an empty
    records list plus a note/blocked explanation — never invent placeholder records."""
    crawler = _FakeDemoCrawler(product_html="<html><body><p>Just a blog post.</p></body></html>")
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/products",
        headers={"X-Forwarded-For": "203.0.113.93"},
        json={"url": "https://example.com"},
    )
    demo_router.reset_state_for_tests()

    payload = resp.json()
    assert resp.status_code == 200
    assert payload["success"] is True
    assert payload["record"]["records"] == []
    assert payload["record"]["note"]


def test_demo_products_rejects_private_or_local_urls_without_running() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/products",
        headers={"X-Forwarded-For": "203.0.113.94"},
        json={"url": "http://127.0.0.1:8421/health"},
    )
    demo_router.reset_state_for_tests()

    assert resp.status_code == 403
    assert crawler.scrape_request is None


def test_demo_products_capacity_full_returns_429_without_running_crawler() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    admission = demo_router.DemoAdmissionController(max_active=0, retry_after_seconds=3)
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    app.dependency_overrides[demo_router.get_demo_admission_controller] = lambda: admission
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/products",
        headers={"X-Forwarded-For": "203.0.113.95"},
        json={"url": "https://example.com"},
    )
    demo_router.reset_state_for_tests()

    assert resp.status_code == 429
    assert crawler.scrape_request is None


# --- Shared quota pool across all four demo endpoints -----------------------------------


def test_demo_all_four_endpoints_share_one_daily_quota_pool_per_ip() -> None:
    """5/day total across scrape+map+crawl+products combined — not 5 each."""
    crawler = _FakeDemoCrawler()
    client_ip = "203.0.113.100"
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    calls = [
        ("/v1/demo/scrape", {"url": "https://example.com"}),
        ("/v1/demo/map", {"url": "https://example.com"}),
        ("/v1/demo/crawl", {"url": "https://example.com"}),
        ("/v1/demo/products", {"url": "https://example.com"}),
        ("/v1/demo/scrape", {"url": "https://example.com"}),
        # 6th call across the shared pool must be rejected regardless of which
        # endpoint it hits.
        ("/v1/demo/products", {"url": "https://example.com"}),
    ]
    statuses = []
    for path, body in calls:
        resp = client.post(path, headers={"X-Forwarded-For": client_ip}, json=body)
        statuses.append(resp.status_code)
    demo_router.reset_state_for_tests()

    assert statuses == [200, 200, 200, 200, 200, 429]


def test_demo_crawl_and_products_count_against_shared_global_ceiling() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    original_ceiling = demo_router.GLOBAL_DAILY_CEILING
    demo_router.GLOBAL_DAILY_CEILING = 2
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    try:
        statuses = []
        endpoints = ["/v1/demo/crawl", "/v1/demo/products", "/v1/demo/crawl"]
        for i, path in enumerate(endpoints):
            resp = client.post(
                path,
                headers={"X-Forwarded-For": f"203.0.113.{110 + i}"},
                json={"url": "https://example.com"},
            )
            statuses.append(resp.status_code)
    finally:
        demo_router.GLOBAL_DAILY_CEILING = original_ceiling
        demo_router.reset_state_for_tests()

    assert statuses == [200, 200, 429]


def test_demo_crawl_and_products_response_never_includes_screenshot_or_raw_html() -> None:
    crawler = _FakeDemoCrawler()
    demo_router.reset_state_for_tests()
    app = _build_demo_app()
    app.dependency_overrides[demo_router.get_demo_crawler] = lambda: crawler
    client = TestClient(app)

    resp = client.post(
        "/v1/demo/products",
        headers={"X-Forwarded-For": "203.0.113.120"},
        json={"url": "https://example.com"},
    )
    demo_router.reset_state_for_tests()

    record = resp.json()["record"]
    assert "screenshot_base64" not in record
    assert "raw_html" not in record
