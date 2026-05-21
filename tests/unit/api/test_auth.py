"""Tests for AuthMiddleware — verifies key-checking and /health bypass."""

from fastapi import FastAPI
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

    @test_app.get("/app")
    async def scout_app() -> dict:
        """Frontend endpoint — no auth."""
        return {"app": "ok"}

    @test_app.get("/favicon.ico")
    async def favicon() -> dict:
        """Browser favicon probe — no auth."""
        return {"icon": "ok"}

    @test_app.get("/docs")
    async def docs() -> dict:
        """Swagger docs endpoint — no auth."""
        return {"docs": "ok"}

    @test_app.get("/openapi.json")
    async def openapi() -> dict:
        """OpenAPI schema endpoint — no auth."""
        return {"openapi": "ok"}

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


def test_frontend_routes_require_no_auth() -> None:
    """Browser-facing frontend routes must not show Unauthorized pages."""
    client = TestClient(_make_app())
    app_resp = client.get("/app")
    favicon_resp = client.get("/favicon.ico")
    docs_resp = client.get("/docs")
    openapi_resp = client.get("/openapi.json")

    assert app_resp.status_code == 200
    assert favicon_resp.status_code == 200
    assert docs_resp.status_code == 200
    assert openapi_resp.status_code == 200


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
