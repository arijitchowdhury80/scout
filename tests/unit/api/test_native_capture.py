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
    """A cleared (non-blocked) capture is run through Scout's Crawl4AI engine
    via structure_capture — the response carries clean markdown + typed records,
    not just the raw text blob."""
    from scout.api.routers import app_browser
    from scout.core.types import CaptureExtraction

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


from scout.api.user_browser import UserBrowserCaptureRequest  # noqa: E402
