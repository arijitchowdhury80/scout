"""POST /harvest — PRISM-callable endpoint that attaches Crawl4AI to a live
browser over CDP and extracts structured records from the cleared tab.

External consumers call this with a CDP URL they manage themselves (not the
Scout UI's browser_service). The tab must already be open and cleared."""

from fastapi.testclient import TestClient

from scout.api.main import app

_HEADERS = {"X-API-Key": "dev-key"}


def test_harvest_returns_structured_output(monkeypatch) -> None:
    from scout.api.routers import harvest
    from scout.core.types import CaptureExtraction

    seen = {}

    async def fake_acquire(cdp_url, url, **kwargs):
        seen["cdp_url"] = cdp_url
        seen["url"] = url
        return CaptureExtraction(
            success=True,
            source_url=url,
            markdown="# Roswell Rentals\n- 101 Oak St",
            records=[{"address": "101 Oak St"}],
            record_count=1,
        )

    monkeypatch.setattr(harvest, "acquire_open_page", fake_acquire)

    client = TestClient(app)
    resp = client.post(
        "/harvest",
        json={"cdp_url": "http://127.0.0.1:9222", "url": "https://zillow.com/roswell"},
        headers=_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["record_count"] == 1
    assert "Oak St" in body["markdown"]
    assert seen["cdp_url"] == "http://127.0.0.1:9222"


def test_harvest_passes_css_schema(monkeypatch) -> None:
    from scout.api.routers import harvest
    from scout.core.types import CaptureExtraction

    seen = {}

    async def fake_acquire(cdp_url, url, **kwargs):
        seen["css_schema"] = kwargs.get("css_schema")
        return CaptureExtraction(success=True, source_url=url, markdown="ok")

    monkeypatch.setattr(harvest, "acquire_open_page", fake_acquire)

    schema = {"name": "listings", "baseSelector": ".card"}
    client = TestClient(app)
    client.post(
        "/harvest",
        json={"cdp_url": "http://127.0.0.1:9222", "url": "https://x.com", "css_schema": schema},
        headers=_HEADERS,
    )
    assert seen["css_schema"] == schema


def test_harvest_empty_cdp_url_returns_failure(monkeypatch) -> None:
    from scout.api.routers import harvest
    from scout.core.types import CaptureExtraction

    async def fake_acquire(cdp_url, url, **kwargs):
        return CaptureExtraction(success=False, error="No CDP endpoint to attach to.")

    monkeypatch.setattr(harvest, "acquire_open_page", fake_acquire)

    client = TestClient(app)
    resp = client.post("/harvest", json={"cdp_url": "", "url": "https://x.com"}, headers=_HEADERS)
    body = resp.json()
    assert body["success"] is False
    assert "CDP" in body["error"]


def test_harvest_requires_api_key() -> None:
    client = TestClient(app)
    resp = client.post(
        "/harvest", json={"cdp_url": "http://127.0.0.1:9222", "url": "https://x.com"}
    )
    assert resp.status_code == 403
