"""Tests for AuthMiddleware — verifies key-checking and /health bypass."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from scout.api.middleware.auth import AuthMiddleware


def _make_app(api_key: str = "test-key", public_hosted_only: bool = False) -> FastAPI:
    """Build a minimal FastAPI app with AuthMiddleware for testing."""
    test_app = FastAPI()
    test_app.add_middleware(
        AuthMiddleware,
        api_key=api_key,
        public_hosted_only=public_hosted_only,
    )

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

    @test_app.get("/api/config")
    async def api_config() -> dict:
        """Frontend config endpoint — no auth."""
        return {"api_key": "test-key"}

    @test_app.post("/scrape")
    async def scrape() -> dict:
        """Scrape endpoint — requires auth."""
        return {"ok": True}

    @test_app.post("/v1/hosted/scrape")
    async def hosted_scrape() -> dict:
        """Hosted routes perform their own Bearer auth."""
        return {"hosted": True}

    @test_app.post("/v1/billing/stripe/webhook")
    async def stripe_webhook() -> dict:
        """Stripe webhook routes perform Stripe signature auth."""
        return {"billing": True}

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
    config_resp = client.get("/api/config")

    assert app_resp.status_code == 200
    assert favicon_resp.status_code == 200
    assert docs_resp.status_code == 200
    assert openapi_resp.status_code == 200
    assert config_resp.status_code == 200


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


def test_hosted_routes_bypass_static_local_key_middleware() -> None:
    """Hosted routes must reach route-level Bearer auth without X-API-Key."""
    client = TestClient(_make_app(api_key="test-key"))

    resp = client.post("/v1/hosted/scrape")

    assert resp.status_code == 200
    assert resp.json()["hosted"] is True


def test_stripe_webhook_bypasses_static_local_key_middleware() -> None:
    """Stripe webhook routes must reach route-level signature auth without X-API-Key."""
    client = TestClient(_make_app(api_key="test-key"))

    resp = client.post("/v1/billing/stripe/webhook")

    assert resp.status_code == 200
    assert resp.json()["billing"] is True


def test_public_hosted_only_blocks_local_routes_even_with_static_key() -> None:
    """Public hosted deployments must not expose local/admin API routes."""
    client = TestClient(_make_app(api_key="test-key", public_hosted_only=True))

    resp = client.post("/scrape", headers={"X-API-Key": "test-key"})

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Local Scout API is disabled in hosted-only mode."


def test_public_hosted_only_blocks_docs_and_frontend_key_config() -> None:
    """Hosted-only mode must not expose public docs or browser key config."""
    client = TestClient(_make_app(api_key="test-key", public_hosted_only=True))

    docs_resp = client.get("/docs")
    openapi_resp = client.get("/openapi.json")
    app_resp = client.get("/app")
    config_resp = client.get("/api/config")
    health_resp = client.get("/health")

    assert docs_resp.status_code == 403
    assert openapi_resp.status_code == 403
    assert app_resp.status_code == 403
    assert config_resp.status_code == 403
    assert health_resp.status_code == 200


def test_public_hosted_only_keeps_hosted_and_billing_routes_available() -> None:
    """Hosted SaaS routes must still reach their own Bearer/signature auth layers."""
    client = TestClient(_make_app(api_key="test-key", public_hosted_only=True))

    hosted_resp = client.post("/v1/hosted/scrape")
    billing_resp = client.post("/v1/billing/stripe/webhook")

    assert hosted_resp.status_code == 200
    assert hosted_resp.json()["hosted"] is True
    assert billing_resp.status_code == 200
    assert billing_resp.json()["billing"] is True
