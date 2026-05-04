"""Tests for AuthMiddleware — verifies key-checking and /health bypass."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from scout.api.middleware.auth import AuthMiddleware


def _make_app(api_key: str = "test-key") -> FastAPI:
    """Build a minimal FastAPI app with AuthMiddleware for testing."""
    test_app = FastAPI()
    test_app.add_middleware(AuthMiddleware, api_key=api_key)

    @test_app.get("/health")
    async def health() -> dict:
        """Health check endpoint — no auth."""
        return {"status": "ok"}

    @test_app.post("/scrape")
    async def scrape() -> dict:
        """Scrape endpoint — requires auth."""
        return {"ok": True}

    return test_app


def test_health_requires_no_auth() -> None:
    """GET /health without X-API-Key must return 200."""
    client = TestClient(_make_app())
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_scrape_without_key_returns_403() -> None:
    """POST /scrape without X-API-Key must return 403."""
    client = TestClient(_make_app())
    resp = client.post("/scrape")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Unauthorized"


def test_scrape_with_wrong_key_returns_403() -> None:
    """POST /scrape with wrong X-API-Key must return 403."""
    client = TestClient(_make_app())
    resp = client.post("/scrape", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Unauthorized"


def test_scrape_with_correct_key_passes_through() -> None:
    """POST /scrape with correct X-API-Key must not return 403."""
    client = TestClient(_make_app(api_key="test-key"))
    resp = client.post("/scrape", headers={"X-API-Key": "test-key"})
    # May be 200 or 422 (missing body) — anything but 403
    assert resp.status_code != 403
