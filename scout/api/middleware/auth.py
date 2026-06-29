"""Authentication middleware — enforces X-API-Key on all non-health routes."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class AuthMiddleware(BaseHTTPMiddleware):
    """Reject requests missing or carrying a wrong X-API-Key header.

    Browser-facing public paths are whitelisted and always pass through.
    """

    def __init__(self, app: object, api_key: str, public_hosted_only: bool = False) -> None:
        """Initialise middleware with the expected API key."""
        super().__init__(app)  # type: ignore[arg-type]
        self._api_key = api_key
        self._public_hosted_only = public_hosted_only

    async def dispatch(self, request: Request, call_next: object) -> Response:
        """Pass public routes through; reject other requests without a valid key."""
        always_public_paths = {
            "/",
            "/beta",
            "/beta.html",
            "/examples",
            "/examples.html",
            "/assets/scout-mark.svg",
            "/assets/scout-product-demo.gif",
            "/assets/scout-wordmark.svg",
            "/favicon.ico",
            "/guide",
            "/guide.html",
            "/health",
            "/legal",
            "/legal.html",
            "/privacy",
            "/privacy.html",
            "/pricing",
            "/pricing.html",
            "/quickstart",
            "/quickstart.html",
            "/status",
            "/status.html",
            "/styles.css",
            "/terms",
            "/terms.html",
            "/third-party-notices",
            "/THIRD_PARTY_NOTICES.md",
        }
        local_browser_public_paths = {
            "/api/config",
            "/app",
            "/app/",
            "/app/live-browser",
            "/docs",
            "/docs/oauth2-redirect",
            "/openapi.json",
            "/redoc",
        }
        if request.url.path in always_public_paths:
            return await call_next(request)  # type: ignore[misc]
        if request.url.path.startswith("/assets/warm-industrial-design-system/"):
            return await call_next(request)  # type: ignore[misc]
        if request.url.path.startswith("/v1/hosted/"):
            return await call_next(request)  # type: ignore[misc]
        if request.url.path.startswith("/v1/billing/stripe/"):
            return await call_next(request)  # type: ignore[misc]
        if self._public_hosted_only:
            return JSONResponse(
                {"detail": "Local Scout API is disabled in hosted-only mode."},
                status_code=403,
            )
        if request.url.path in local_browser_public_paths:
            return await call_next(request)  # type: ignore[misc]

        incoming_key = request.headers.get("X-API-Key")
        if not incoming_key or incoming_key != self._api_key:
            return JSONResponse({"detail": "Unauthorized"}, status_code=403)

        return await call_next(request)  # type: ignore[misc]
