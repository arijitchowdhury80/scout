"""Tests for the anonymous PLG homepage demo endpoint (/v1/demo/*).

Spec: docs/product/plg-playground-ux.md — anonymous "taste" tier.
- POST /v1/demo/scrape and POST /v1/demo/map — no auth.
- Fast endpoints only (never crawl/products/company/screenshot).
- 5 runs / client IP / day, plus a global daily ceiling.
- Preview output: truncated, with an upsell flag/message.
- Blocks unsafe/private targets via the existing hosted URL-safety check.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from scout.api.routers import demo as demo_router
from scout.core.types import MapResponse, ScoutMetadata, ScrapeResponse


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


class _FakeDemoCrawler:
    def __init__(self) -> None:
        self.scrape_request = None
        self.map_request = None

    async def scrape(self, req):
        self.scrape_request = req
        markdown = "# Demo Company\n\n" + ("Useful evidence-grade content. " * 200)
        return ScrapeResponse(
            success=True,
            url=req.url,
            markdown=markdown,
            raw_markdown=markdown,
            clean_markdown=markdown,
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
    """The demo router only exposes scrape + map — no crawl/products/company/screenshot routes."""
    app = _build_demo_app()
    client = TestClient(app)
    for path in (
        "/v1/demo/crawl",
        "/v1/demo/products",
        "/v1/demo/company",
        "/v1/demo/screenshot",
    ):
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
    """Documented invariant: demo router must never wire crawl/products/company/screenshot."""
    assert demo_router.ALLOWED_WORKFLOWS == {"scrape", "map"}
