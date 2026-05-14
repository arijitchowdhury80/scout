"""Tests for Scout API routers — uses TestClient with mocked ScoutCrawler."""

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from scout.api.main import app, get_crawler
from scout.core.types import (
    AlgoliaProductRecord,
    CrawlPage,
    CrawlResponse,
    ExtractResponse,
    MapResponse,
    ProductCrawlResponse,
    ProductSource,
    ScoutMetadata,
    ScrapeResponse,
    ScreenshotResponse,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_API_KEY = "dev-key"
_HEADERS = {"X-API-Key": _API_KEY}

_TS = "2026-05-03T10:00:00Z"


def _meta(url: str = "https://example.com") -> ScoutMetadata:
    """Build a minimal ScoutMetadata for tests."""
    return ScoutMetadata(url=url, crawled_at=_TS)


# ---------------------------------------------------------------------------
# /scrape
# ---------------------------------------------------------------------------


def test_scrape_returns_200_with_mock_crawler() -> None:
    """POST /scrape with valid body and mocked crawler returns 200."""
    mock_crawler = MagicMock()
    mock_crawler.scrape = AsyncMock(
        return_value=ScrapeResponse(
            success=True,
            url="https://example.com",
            markdown="# Hello",
            metadata=_meta(),
            duration_ms=100,
        )
    )
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    try:
        client = TestClient(app)
        resp = client.post("/scrape", json={"url": "https://example.com"}, headers=_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["url"] == "https://example.com"
        assert data["markdown"] == "# Hello"
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# /crawl
# ---------------------------------------------------------------------------


def test_crawl_returns_200_with_mock_crawler() -> None:
    """POST /crawl with valid body and mocked crawler returns 200."""
    mock_crawler = MagicMock()
    mock_crawler.crawl = AsyncMock(
        return_value=CrawlResponse(
            success=True,
            start_url="https://example.com",
            pages=[
                CrawlPage(
                    url="https://example.com",
                    markdown="# Home",
                    metadata=_meta(),
                    success=True,
                )
            ],
            total_pages=1,
            duration_ms=200,
        )
    )
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    try:
        client = TestClient(app)
        resp = client.post("/crawl", json={"url": "https://example.com"}, headers=_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["start_url"] == "https://example.com"
        assert data["total_pages"] == 1
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# /extract
# ---------------------------------------------------------------------------


def test_extract_returns_200_with_mock_crawler() -> None:
    """POST /extract with valid body and mocked crawler returns 200."""
    mock_crawler = MagicMock()
    mock_crawler.extract = AsyncMock(
        return_value=ExtractResponse(
            success=True,
            url="https://example.com",
            data={"name": "Acme"},
            metadata=_meta(),
            duration_ms=300,
        )
    )
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    try:
        client = TestClient(app)
        resp = client.post(
            "/extract",
            json={
                "url": "https://example.com",
                "schema": {"name": "str"},
                "instruction": "extract company name",
            },
            headers=_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"] == {"name": "Acme"}
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# /map
# ---------------------------------------------------------------------------


def test_map_returns_200_with_mock_crawler() -> None:
    """POST /map with valid body and mocked crawler returns 200."""
    mock_crawler = MagicMock()
    mock_crawler.map_urls = AsyncMock(
        return_value=MapResponse(
            success=True,
            start_url="https://example.com",
            urls=["https://example.com/a", "https://example.com/b"],
            total=2,
            duration_ms=50,
        )
    )
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    try:
        client = TestClient(app)
        resp = client.post("/map", json={"url": "https://example.com"}, headers=_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["total"] == 2
        assert len(data["urls"]) == 2
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# /screenshot
# ---------------------------------------------------------------------------


def test_screenshot_returns_200_with_mock_crawler() -> None:
    """POST /screenshot with valid body and mocked crawler returns 200."""
    mock_crawler = MagicMock()
    mock_crawler.screenshot = AsyncMock(
        return_value=ScreenshotResponse(
            success=True,
            url="https://example.com",
            screenshot_base64="abc123",
            width=1280,
            height=800,
            duration_ms=400,
        )
    )
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    try:
        client = TestClient(app)
        resp = client.post(
            "/screenshot",
            json={"url": "https://example.com"},
            headers=_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["width"] == 1280
        assert data["height"] == 800
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# /products
# ---------------------------------------------------------------------------


def test_products_returns_200_with_mock_crawler() -> None:
    """POST /products with valid body and mocked crawler returns Algolia records."""
    mock_crawler = MagicMock()
    mock_crawler.products = AsyncMock(
        return_value=ProductCrawlResponse(
            success=True,
            query="men shirts",
            site="shop.example.com",
            start_url="https://shop.example.com",
            records=[
                AlgoliaProductRecord(
                    objectID="abc123",
                    name="Oxford Shirt",
                    url="https://shop.example.com/products/oxford",
                    source=ProductSource(
                        url="https://shop.example.com/products/oxford",
                        extractor="jsonld",
                    ),
                )
            ],
            total_records=1,
            duration_ms=500,
        )
    )
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    try:
        client = TestClient(app)
        resp = client.post(
            "/products",
            json={"query": "men shirts", "site": "shop.example.com"},
            headers=_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["records"][0]["objectID"] == "abc123"
        assert data["records"][0]["_source"]["extractor"] == "jsonld"
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


def test_health_returns_version_info() -> None:
    """GET /health returns status + version fields."""
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "crawl4ai_version" in data
    assert "scout_version" in data


def test_root_returns_html_landing_page() -> None:
    """GET / returns a simple service page for browser users."""
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Scout" in resp.text
    assert "/docs" in resp.text
