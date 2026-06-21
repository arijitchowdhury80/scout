"""Integration tests — capture structuring against REAL Crawl4AI.

Launches a real Playwright browser but performs NO network fetch: the HTML is
processed via Crawl4AI's `raw://` scheme. SLOW (~2-10s each).

Run: pytest tests/integration/test_capture_extract_live.py -v -m integration

What these prove that unit tests (mocks) cannot:
- crawl4ai 0.7.7 `raw://` actually ingests a held HTML string and yields markdown
- the `result.markdown.fit_markdown` path resolves on a raw:// result
- JsonCssExtractionStrategy returns typed per-item records from raw HTML, no LLM
- no network fetch occurs — HTML referencing an unreachable host still structures
"""

import pytest

from scout.core.capture_extract import structure_capture
from scout.core.types import CaptureExtraction

# Mimics a cleared listings page captured from a human-solved native window.
# References a non-resolvable host on purpose: if structuring tried to FETCH it
# the test would fail, proving we only process the bytes we already hold.
_CAPTURED_HTML = """
<html><head><title>Roswell Rentals</title></head>
<body>
  <h1>Rentals in Roswell, GA</h1>
  <ul class="listings">
    <li class="card"><span class="addr">101 Oak St</span><span class="price">$2,100</span></li>
    <li class="card"><span class="addr">202 Pine Ave</span><span class="price">$1,850</span></li>
    <li class="card"><span class="addr">303 Maple Dr</span><span class="price">$2,400</span></li>
  </ul>
  <a href="https://unreachable.invalid/next">next page</a>
</body></html>
"""


@pytest.mark.integration
async def test_raw_capture_yields_markdown_without_fetch():
    """Real crawl4ai `raw://` turns held HTML into clean markdown, no network."""
    resp = await structure_capture(_CAPTURED_HTML, source_url="https://zillow.com/roswell")

    assert isinstance(resp, CaptureExtraction)
    assert resp.success is True, f"structuring failed: {resp.error}"
    assert "Roswell" in resp.markdown
    assert resp.word_count > 0
    assert resp.source_url == "https://zillow.com/roswell"


@pytest.mark.integration
async def test_raw_capture_css_schema_returns_typed_records():
    """A CSS schema extracts one typed record per listing card — no LLM."""
    css_schema = {
        "name": "rentals",
        "baseSelector": "li.card",
        "fields": [
            {"name": "address", "selector": ".addr", "type": "text"},
            {"name": "price", "selector": ".price", "type": "text"},
        ],
    }
    resp = await structure_capture(_CAPTURED_HTML, css_schema=css_schema)

    assert resp.success is True, f"structuring failed: {resp.error}"
    assert resp.record_count == 3, f"expected 3 records, got {resp.records}"
    addresses = {r.get("address") for r in resp.records}
    assert "101 Oak St" in addresses
    assert any("2,100" in (r.get("price") or "") for r in resp.records)
