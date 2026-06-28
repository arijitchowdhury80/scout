"""Native-window capture endpoint: the fallback rung for behavioral walls
(PerimeterX press-and-hold) that the embedded canvas can't clear. Captures the
active tab of the Scout-managed native Chrome and reports a block verdict so the
UI can say "still blocked — solve it, then capture again."
"""

from fastapi.testclient import TestClient

from scout.api.main import app
from scout.api.user_browser import UserBrowserSessionState, browser_service

_HEADERS = {"X-API-Key": "dev-key"}


def test_capture_without_open_session_returns_graceful_error() -> None:
    # Reset the module singleton so this test doesn't depend on whether another
    # test opened a session first (full-suite ordering).
    browser_service._state = UserBrowserSessionState(connected=False, status="not_started")

    client = TestClient(app)
    resp = client.post(
        "/app/browser/capture", json={"url": "https://zillow.com/x"}, headers=_HEADERS
    )
    assert resp.status_code == 200
    body = resp.json()
    # No native Chrome session open → structured error, not a 500.
    assert body["error"]
    assert body["blocked"] is False


def test_capture_requires_api_key() -> None:
    client = TestClient(app)
    resp = client.post("/app/browser/capture", json={"url": "https://x.com"})
    assert resp.status_code == 403


def test_capture_structures_cleared_page_into_records(monkeypatch) -> None:
    """With NO live CDP port, a cleared (non-blocked) capture falls back to
    structuring the static snapshot via raw:// (structure_capture) — the
    response carries clean markdown + typed records, not just the text blob."""
    from scout.api.routers import app_browser
    from scout.core.types import CaptureExtraction

    # No open session → no debugging_port → fall back to the raw:// snapshot path.
    browser_service._state = UserBrowserSessionState(connected=False, status="not_started")

    async def fake_capture(_url: str):
        return UserBrowserCaptureRequest(
            url="https://zillow.com/roswell",
            title="Roswell Rentals",
            html="<li class='card'>101 Oak St $2,100</li>",
            text="101 Oak St $2,100",
        )

    async def fake_structure(html, **kwargs):
        assert "Oak St" in html  # structuring the HELD html, not re-fetching
        return CaptureExtraction(
            success=True,
            source_url=kwargs.get("source_url", ""),
            markdown="# Roswell Rentals\n- 101 Oak St — $2,100",
            records=[{"address": "101 Oak St", "price": "$2,100"}],
            record_count=1,
            word_count=6,
        )

    monkeypatch.setattr(app_browser.browser_service, "capture_active_tab", fake_capture)
    monkeypatch.setattr(app_browser, "structure_capture", fake_structure)

    client = TestClient(app)
    resp = client.post(
        "/app/browser/capture",
        json={
            "url": "https://zillow.com/roswell",
            "css_schema": {
                "name": "rentals",
                "baseSelector": "li.card",
                "fields": [{"name": "address", "selector": ".card", "type": "text"}],
            },
        },
        headers=_HEADERS,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["blocked"] is False
    assert body["record_count"] == 1
    assert body["records"][0]["address"] == "101 Oak St"
    assert "Oak St" in body["markdown"]


def test_capture_product_dom_returns_algolia_records(monkeypatch) -> None:
    """A cleared product category captured from the user browser should be
    product-aware without asking the user to write CSS selectors."""
    from scout.api.routers import app_browser
    from scout.core.types import CaptureExtraction

    browser_service._state = UserBrowserSessionState(connected=False, status="not_started")

    async def fake_capture(_url: str):
        return UserBrowserCaptureRequest(
            url="https://www.esteelauder.com/products/681/product-catalog/skin-care",
            title="Skincare",
            html="""
            <article class="product-grid__item">
              <a class="product-tile__link"
                 href="/product/681/141225/product-catalog/skincare/advanced-night-repair-serum">
                <img alt="Advanced Night Repair Serum" src="/media/anr.jpg">
                <span class="price">$85.00</span>
              </a>
            </article>
            """,
            text="Advanced Night Repair Serum $85.00",
        )

    async def fake_structure(html, **kwargs):
        return CaptureExtraction(
            success=True,
            source_url=kwargs.get("source_url", ""),
            markdown="# Skincare\nAdvanced Night Repair Serum $85.00",
            word_count=6,
        )

    monkeypatch.setattr(app_browser.browser_service, "capture_active_tab", fake_capture)
    monkeypatch.setattr(app_browser, "structure_capture", fake_structure)

    client = TestClient(app)
    resp = client.post(
        "/app/browser/capture",
        json={
            "url": "https://www.esteelauder.com/products/681/product-catalog/skin-care",
            "record_type": "products",
            "category_name": "Skin Care",
            "limit": 3,
        },
        headers=_HEADERS,
    )

    body = resp.json()
    assert body["blocked"] is False
    assert body["record_count"] == 1
    record = body["records"][0]
    assert record["objectID"]
    assert record["name"] == "Advanced Night Repair Serum"
    assert record["price"] == 85.0
    assert record["citations"][0]["source_url"] == (
        "https://www.esteelauder.com/products/681/product-catalog/skin-care"
    )


def test_capture_skips_structuring_when_still_blocked(monkeypatch) -> None:
    """A still-blocked capture is NOT structured — no records, the UI tells the
    human to solve the wall first."""
    from scout.api.routers import app_browser

    async def fake_capture(_url: str):
        return UserBrowserCaptureRequest(
            url="https://zillow.com/roswell",
            title="Access to this page has been denied",
            html="<div>press and hold</div>",
            text="Access to this page has been denied. Press and hold.",
        )

    called = {"structured": False}

    async def fake_structure(html, **kwargs):  # pragma: no cover - must NOT run
        called["structured"] = True
        raise AssertionError("structure_capture should not run on a blocked page")

    monkeypatch.setattr(app_browser.browser_service, "capture_active_tab", fake_capture)
    monkeypatch.setattr(app_browser, "structure_capture", fake_structure)

    client = TestClient(app)
    resp = client.post(
        "/app/browser/capture", json={"url": "https://zillow.com/roswell"}, headers=_HEADERS
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["blocked"] is True
    assert body["record_count"] == 0
    assert body["records"] == []
    assert called["structured"] is False


def test_capture_prefers_crawl4ai_over_cdp_for_live_tab(monkeypatch) -> None:
    """When a live CDP port is open, the cleared tab is driven by Crawl4AI over
    CDP (acquire_open_page) — the CORE engine on the live, fully-rendered page —
    NOT the static raw:// snapshot. structure_capture must not run."""
    from scout.api.routers import app_browser
    from scout.core.types import CaptureExtraction

    browser_service._state = UserBrowserSessionState(
        connected=True, status="opened", debugging_port=49321
    )

    async def fake_capture(_url: str):
        return UserBrowserCaptureRequest(
            url="https://zillow.com/roswell",
            title="Roswell Rentals",
            html="<li class='card'>snapshot</li>",
            text="snapshot",
        )

    seen = {"cdp_url": "", "structured": False}

    async def fake_acquire(cdp_url, url, **kwargs):
        seen["cdp_url"] = cdp_url
        return CaptureExtraction(
            success=True,
            source_url=url,
            markdown="# Roswell Rentals (live)",
            records=[{"address": "101 Oak St"}],
            record_count=1,
            word_count=4,
        )

    async def fake_structure(html, **kwargs):  # pragma: no cover - must NOT run
        seen["structured"] = True
        raise AssertionError("snapshot fallback must not run when CDP acquire succeeds")

    monkeypatch.setattr(app_browser.browser_service, "capture_active_tab", fake_capture)
    monkeypatch.setattr(app_browser, "acquire_open_page", fake_acquire)
    monkeypatch.setattr(app_browser, "structure_capture", fake_structure)

    client = TestClient(app)
    resp = client.post(
        "/app/browser/capture", json={"url": "https://zillow.com/roswell"}, headers=_HEADERS
    )

    body = resp.json()
    assert body["record_count"] == 1
    assert body["records"][0]["address"] == "101 Oak St"
    assert "live" in body["markdown"]
    assert seen["cdp_url"] == "http://127.0.0.1:49321"
    assert seen["structured"] is False


def test_capture_falls_back_to_snapshot_when_cdp_acquire_fails(monkeypatch) -> None:
    """If Crawl4AI-over-CDP fails on the live tab, fall back to structuring the
    static snapshot via raw:// — still the core engine, never raw text."""
    from scout.api.routers import app_browser
    from scout.core.types import CaptureExtraction

    browser_service._state = UserBrowserSessionState(
        connected=True, status="opened", debugging_port=49321
    )

    async def fake_capture(_url: str):
        return UserBrowserCaptureRequest(
            url="https://zillow.com/roswell",
            title="Roswell Rentals",
            html="<li class='card'>snapshot html</li>",
            text="snapshot",
        )

    async def fake_acquire(cdp_url, url, **kwargs):
        return CaptureExtraction(success=False, source_url=url, error="cdp attach failed")

    async def fake_structure(html, **kwargs):
        assert "snapshot html" in html
        return CaptureExtraction(
            success=True,
            source_url=kwargs.get("source_url", ""),
            markdown="# from snapshot",
            records=[{"address": "fallback"}],
            record_count=1,
        )

    monkeypatch.setattr(app_browser.browser_service, "capture_active_tab", fake_capture)
    monkeypatch.setattr(app_browser, "acquire_open_page", fake_acquire)
    monkeypatch.setattr(app_browser, "structure_capture", fake_structure)

    client = TestClient(app)
    resp = client.post(
        "/app/browser/capture", json={"url": "https://zillow.com/roswell"}, headers=_HEADERS
    )

    body = resp.json()
    assert body["record_count"] == 1
    assert body["records"][0]["address"] == "fallback"
    assert "snapshot" in body["markdown"]


from scout.api.user_browser import UserBrowserCaptureRequest  # noqa: E402
