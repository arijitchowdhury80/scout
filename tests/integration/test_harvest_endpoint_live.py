"""Integration test — POST /harvest endpoint with REAL Crawl4AI + real Chromium.

Proves the HTTP layer correctly wires through to acquire_open_page over CDP.
Launches a real browser, injects a DOM marker, calls /harvest, verifies the
marker survives (proving no re-navigation).

SLOW (~5-15s); needs Playwright chromium. Run:
  pytest tests/integration/test_harvest_endpoint_live.py -v -m integration
"""

import pytest
from fastapi.testclient import TestClient

from scout.api.main import app

_HEADERS = {"X-API-Key": "dev-key"}
_PORT = 49734
_MARKER = "SCOUT-HARVEST-ENDPOINT-MARKER-9b2c"


@pytest.mark.integration
async def test_harvest_endpoint_reads_live_tab():
    """POST /harvest with real CDP → real Crawl4AI extraction from live tab."""
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=[f"--remote-debugging-port={_PORT}"])
        try:
            page = await browser.new_page()
            await page.goto("https://example.com", wait_until="domcontentloaded")
            await page.evaluate(
                f"document.body.insertAdjacentHTML('afterbegin',"
                f" '<div id=harvest-marker>{_MARKER}</div>')"
            )

            client = TestClient(app)
            resp = client.post(
                "/harvest",
                json={
                    "cdp_url": f"http://127.0.0.1:{_PORT}",
                    "url": "https://example.com",
                },
                headers=_HEADERS,
            )
        finally:
            await browser.close()

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True, f"harvest failed: {body['error']}"
    assert _MARKER in body["markdown"], (
        "marker missing — Crawl4AI re-navigated instead of reading in place"
    )
    assert "example" in body["markdown"].lower()


@pytest.mark.integration
def test_harvest_endpoint_empty_cdp_returns_failure():
    """POST /harvest with empty cdp_url → honest failure."""
    client = TestClient(app)
    resp = client.post(
        "/harvest",
        json={"cdp_url": "", "url": "https://example.com"},
        headers=_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert "CDP" in body["error"]
