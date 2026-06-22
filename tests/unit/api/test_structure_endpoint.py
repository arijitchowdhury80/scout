"""POST /structure — PRISM-callable endpoint that structures raw HTML into
markdown + typed records via Crawl4AI (raw:// scheme, no network fetch).

This is the programmatic API surface for external consumers. The /app/browser/*
endpoints are UI-specific; this one takes HTML directly."""

from fastapi.testclient import TestClient

from scout.api.main import app

_HEADERS = {"X-API-Key": "dev-key"}


def test_structure_returns_markdown_from_html(monkeypatch) -> None:
    from scout.api.routers import structure
    from scout.core.types import CaptureExtraction

    async def fake_structure(html, **kwargs):
        return CaptureExtraction(
            success=True,
            source_url=kwargs.get("source_url", ""),
            markdown="# Products\n- Widget A",
            word_count=4,
        )

    monkeypatch.setattr(structure, "structure_capture", fake_structure)

    client = TestClient(app)
    resp = client.post(
        "/structure",
        json={"html": "<div>Widget A</div>", "source_url": "https://example.com"},
        headers=_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "Widget" in body["markdown"]


def test_structure_with_css_schema_returns_records(monkeypatch) -> None:
    from scout.api.routers import structure
    from scout.core.types import CaptureExtraction

    async def fake_structure(html, **kwargs):
        return CaptureExtraction(
            success=True,
            source_url="https://x.com",
            markdown="# Items",
            records=[{"name": "A"}, {"name": "B"}],
            record_count=2,
        )

    monkeypatch.setattr(structure, "structure_capture", fake_structure)

    client = TestClient(app)
    resp = client.post(
        "/structure",
        json={
            "html": "<li>A</li><li>B</li>",
            "css_schema": {"name": "items", "baseSelector": "li"},
        },
        headers=_HEADERS,
    )
    body = resp.json()
    assert body["record_count"] == 2
    assert body["records"][0]["name"] == "A"


def test_structure_empty_html_returns_failure(monkeypatch) -> None:
    from scout.api.routers import structure
    from scout.core.types import CaptureExtraction

    async def fake_structure(html, **kwargs):
        return CaptureExtraction(success=False, error="Cannot structure an empty capture.")

    monkeypatch.setattr(structure, "structure_capture", fake_structure)

    client = TestClient(app)
    resp = client.post("/structure", json={"html": ""}, headers=_HEADERS)
    body = resp.json()
    assert body["success"] is False
    assert body["error"]


def test_structure_requires_api_key() -> None:
    client = TestClient(app)
    resp = client.post("/structure", json={"html": "<p>hi</p>"})
    assert resp.status_code == 403
