"""Integration test — PROVE Crawl4AI-over-CDP reads an already-open tab WITHOUT
re-navigating it.

The whole human-assisted architecture depends on this: after a human clears a
wall, Crawl4AI must drive THAT cleared tab without a fresh navigation (which
would re-trigger the wall). This test launches a real Chromium with a debug
port, loads a page, injects a UNIQUE MARKER into the live DOM, then runs
acquire_open_page(js_only=True). If the marker survives into the structured
output, Crawl4AI read the existing tab in place — a goto() would have reloaded
the page and wiped the marker.

SLOW (~5-15s); needs Playwright chromium. Run:
  pytest tests/integration/test_cdp_acquire_live.py -v -m integration
"""

import pytest

from scout.core.cdp_acquire import acquire_open_page
from scout.core.types import CaptureExtraction

_PORT = 49733
_MARKER = "SCOUT-CLEARED-SESSION-MARKER-7f3a"


@pytest.mark.integration
async def test_crawl4ai_reads_existing_tab_without_navigating():
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=[f"--remote-debugging-port={_PORT}"])
        try:
            page = await browser.new_page()
            await page.goto("https://example.com", wait_until="domcontentloaded")
            # Mutate the LIVE DOM. A re-navigation (goto) would wipe this; reading
            # the existing tab in place preserves it.
            await page.evaluate(
                f"document.body.insertAdjacentHTML('afterbegin',"
                f" '<div id=scout-marker>{_MARKER}</div>')"
            )

            resp = await acquire_open_page(f"http://127.0.0.1:{_PORT}", "https://example.com")
        finally:
            await browser.close()

    assert isinstance(resp, CaptureExtraction)
    assert resp.success is True, f"acquisition failed: {resp.error}"
    # The injected marker proves no re-navigation happened.
    assert _MARKER in resp.markdown, (
        "marker missing — Crawl4AI re-navigated the tab instead of reading it in "
        "place (js_only failed to suppress goto)"
    )
    # And it still produced real page content through the core pipeline.
    assert "example" in resp.markdown.lower()
