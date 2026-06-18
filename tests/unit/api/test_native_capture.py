"""Native-window capture endpoint: the fallback rung for behavioral walls
(PerimeterX press-and-hold) that the embedded canvas can't clear. Captures the
active tab of the Scout-managed native Chrome and reports a block verdict so the
UI can say "still blocked — solve it, then capture again."
"""

from fastapi.testclient import TestClient

from scout.api.main import app

_HEADERS = {"X-API-Key": "dev-key"}


def test_capture_without_open_session_returns_graceful_error() -> None:
    client = TestClient(app)
    resp = client.post("/app/browser/capture", json={"url": "https://zillow.com/x"}, headers=_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    # No native Chrome session open in a unit test → structured error, not a 500.
    assert body["error"]
    assert body["blocked"] is False


def test_capture_requires_api_key() -> None:
    client = TestClient(app)
    resp = client.post("/app/browser/capture", json={"url": "https://x.com"})
    assert resp.status_code == 403
