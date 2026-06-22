"""Integration test — POST /structure endpoint with REAL Crawl4AI.

Proves the HTTP layer correctly wires through to structure_capture and returns
structured markdown + typed records via the raw:// scheme. No mocks.

SLOW (~2-10s). Run:
  pytest tests/integration/test_structure_endpoint_live.py -v -m integration
"""

import pytest
from fastapi.testclient import TestClient

from scout.api.main import app

_HEADERS = {"X-API-Key": "dev-key"}

_HTML = """
<html><head><title>Test Products</title></head>
<body>
  <ul class="products">
    <li class="item"><span class="name">Widget A</span><span class="price">$10</span></li>
    <li class="item"><span class="name">Widget B</span><span class="price">$20</span></li>
  </ul>
</body></html>
"""


@pytest.mark.integration
def test_structure_endpoint_returns_real_markdown():
    """POST /structure with real HTML → real Crawl4AI markdown, no mocks."""
    client = TestClient(app)
    resp = client.post(
        "/structure",
        json={"html": _HTML, "source_url": "https://example.com/products"},
        headers=_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True, f"structuring failed: {body['error']}"
    assert "Widget" in body["markdown"]
    assert body["word_count"] > 0


@pytest.mark.integration
def test_structure_endpoint_css_schema_returns_typed_records():
    """POST /structure with CSS schema → typed per-item records from real Crawl4AI."""
    client = TestClient(app)
    resp = client.post(
        "/structure",
        json={
            "html": _HTML,
            "css_schema": {
                "name": "products",
                "baseSelector": "li.item",
                "fields": [
                    {"name": "name", "selector": ".name", "type": "text"},
                    {"name": "price", "selector": ".price", "type": "text"},
                ],
            },
        },
        headers=_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True, f"structuring failed: {body['error']}"
    assert body["record_count"] == 2
    names = {r["name"] for r in body["records"]}
    assert "Widget A" in names
    assert "Widget B" in names


@pytest.mark.integration
def test_structure_endpoint_empty_html_returns_failure():
    """POST /structure with empty HTML → honest failure, no crash."""
    client = TestClient(app)
    resp = client.post("/structure", json={"html": ""}, headers=_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert body["error"]
