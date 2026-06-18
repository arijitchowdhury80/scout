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
    assert "kind: \"input\"" in body or 'kind: "input"' in body
    assert "__SCOUT_API_KEY__" not in body  # placeholder was replaced
