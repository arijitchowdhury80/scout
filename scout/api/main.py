"""Scout FastAPI application — entry point for the HTTP service."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import Response

from scout.api.config import settings
from scout.api.hosted_llm_policy import resolve_hosted_llm_api_key
from scout.api.deps import get_crawler
from scout.api.middleware.auth import AuthMiddleware
from scout.api import launch_site
from scout.api.routers import (
    algolia,
    app_browser,
    app_runs,
    billing,
    crawl,
    extract,
    harvest,
    health,
    products,
    playground,
    run,
    runs,
    structure,
    workdir,
    hosted,
)
from scout.api.routers import map as map_router
from scout.api.routers import scrape, screenshot
from scout.core.crawler import ScoutCrawler

# Re-export get_crawler so tests can import it from scout.api.main for
# dependency_overrides.
__all__ = ["app", "get_crawler"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise shared resources on startup; release them on shutdown."""
    from pathlib import Path

    from scout.api.db import RunDB
    from scout.api.run_store import bind_db
    from scout.core.platform.account_service import HostedAccountService
    from scout.core.platform.account_sqlite_store import SQLiteHostedAccountStore
    from scout.core.platform.key_delivery import (
        SmtpHostedApiKeyDeliveryConfig,
        SmtpHostedApiKeyDeliveryService,
    )
    from scout.core.platform.payment_provisioning import (
        HostedPaymentProvisioningService,
        SQLiteHostedPaymentStore,
    )
    from scout.core.platform.hosted_rate_limit import HostedRateLimitConfig, HostedRateLimiter
    from scout.core.platform.stripe_checkout import StripeCheckoutConfig, StripeCheckoutService

    app.state.crawler = ScoutCrawler(llm_api_key=resolve_hosted_llm_api_key(settings))
    db_path = settings.resolve_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    run_db = RunDB(db_path)
    await run_db.init_db()
    app.state.run_db = run_db
    hosted_db_path = settings.resolve_hosted_account_db_path()
    Path(hosted_db_path).parent.mkdir(parents=True, exist_ok=True)
    hosted_account_service = HostedAccountService(SQLiteHostedAccountStore(hosted_db_path))
    app.state.hosted_account_service = hosted_account_service
    app.state.hosted_payment_service = HostedPaymentProvisioningService(
        hosted_account_service,
        SQLiteHostedPaymentStore(hosted_db_path),
    )
    app.state.hosted_rate_limiter = HostedRateLimiter(
        HostedRateLimitConfig(
            max_requests=settings.hosted_rate_limit_max_requests,
            window_seconds=settings.hosted_rate_limit_window_seconds,
        )
    )
    app.state.hosted_key_delivery_service = SmtpHostedApiKeyDeliveryService(
        SmtpHostedApiKeyDeliveryConfig(
            host=settings.hosted_key_delivery_smtp_host,
            port=settings.hosted_key_delivery_smtp_port,
            from_email=settings.hosted_key_delivery_smtp_from_email,
            username=settings.hosted_key_delivery_smtp_username,
            password=settings.hosted_key_delivery_smtp_password,
            use_tls=settings.hosted_key_delivery_smtp_use_tls,
        )
    )
    app.state.stripe_checkout_service = StripeCheckoutService(
        StripeCheckoutConfig(
            secret_key=settings.stripe_secret_key,
            beta_price_id=settings.stripe_beta_price_id,
            success_url=settings.stripe_success_url,
            cancel_url=settings.stripe_cancel_url,
        )
    )
    bind_db(run_db)
    yield
    await run_db.close()


app = FastAPI(
    title="Scout",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    AuthMiddleware,
    api_key=settings.scout_api_key,
    public_hosted_only=settings.scout_public_hosted_only,
)

app.include_router(health.router)
app.include_router(scrape.router)
app.include_router(crawl.router)
app.include_router(extract.router)
app.include_router(structure.router)
app.include_router(harvest.router)
app.include_router(products.router)
app.include_router(playground.router)
app.include_router(run.router)
app.include_router(runs.router)
app.include_router(algolia.router)
app.include_router(app_browser.router)
app.include_router(app_runs.router)
app.include_router(map_router.router)
app.include_router(screenshot.router)
app.include_router(workdir.router)
app.include_router(hosted.router)
app.include_router(billing.router)
app.include_router(launch_site.router)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    """Return an empty favicon response to keep browser probes quiet."""
    return Response(status_code=204)
