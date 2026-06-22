"""The embedded-browser console page must serve, be public (browser nav, no
header), embed the API key, and wire the canvas to the /app/live WebSocket.
"""

from fastapi.testclient import TestClient

from scout.api.main import app


def test_live_browser_page_is_public_and_renders() -> None:
    client = TestClient(app)
    resp = client.get("/app/live-browser")  # no X-API-Key header on purpose
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    body = resp.text
    assert "<canvas" in body
    assert "/app/live" in body  # connects to the WS bridge
    assert 'kind: "input"' in body or 'kind: "input"' in body
    assert "__SCOUT_API_KEY__" not in body  # placeholder was replaced


def test_native_grab_shows_structured_markdown_not_raw_blob() -> None:
    """The nativeGrab JS must use res.markdown for display/download/preview,
    not the raw res.text blob. The API already returns structured markdown —
    the UI must surface it."""
    client = TestClient(app)
    body = client.get("/app/live-browser").text
    # The JS must reference res.markdown (the structured output) not just res.text
    assert "res.markdown" in body, "nativeGrab must use res.markdown for display"
    # Download button should download markdown, not raw text
    assert "scout-capture.md" in body, "download should produce .md not .txt"


def test_native_grab_shows_record_count() -> None:
    """When the API returns records, the captured bar must show the count."""
    client = TestClient(app)
    body = client.get("/app/live-browser").text
    assert "res.record_count" in body or "record_count" in body, (
        "captured bar must show record count from the API response"
    )


def test_native_grab_offers_records_download() -> None:
    """When records exist, the UI must offer a JSON download for the typed records."""
    client = TestClient(app)
    body = client.get("/app/live-browser").text
    assert "downloadRecords" in body or "records-download" in body, (
        "UI must have a download-records button/action"
    )
    assert "application/json" in body, "records download must be JSON"
