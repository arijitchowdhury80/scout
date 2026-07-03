"""Hosted API routes protected by Scout hosted Bearer keys."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, EmailStr

from scout.api.config import settings
from scout.api.deps import (
    get_crawler,
    get_crawler_optional,
    get_hosted_admission_controller,
    get_hosted_account_service,
    get_hosted_job_queue,
    get_hosted_key_delivery_service,
    get_hosted_payment_provisioning_service,
    get_hosted_rate_limiter,
)
from scout.api.hosted_jobs import HostedJobQueue, HostedQueueFull
from scout.api.run_store import remember_run
from scout.api.run_store import get_run, list_runs
from scout.api.run_store import StoredRun
from scout.core.crawler import ScoutCrawler
from scout.core.platform.account_service import HostedAccountService
from scout.core.platform.admission import AdmissionController, AdmissionRejected
from scout.core.platform.hosted import (
    HostedAction,
    HostedPlan,
    HostedPlanLimits,
    HostedUsageBalance,
    plan_limits,
)
from scout.core.platform.hosted_rate_limit import HostedRateLimiter
from scout.core.platform.key_delivery import (
    HostedApiKeyDeliveryRequest,
    HostedApiKeyDeliveryService,
)
from scout.core.platform.payment_provisioning import HostedPaymentProvisioningService
from scout.core.platform.run import run_use_case
from scout.core.platform.types import RunRequest, RunResponse
from scout.core.platform.url_safety import validate_hosted_url_fields
from scout.core.platform.url_safety import validate_hosted_url_with_dns
from scout.core.platform.workspace import resolve_run_output_dir
from scout.core.types import (
    CrawlRequest,
    CrawlResponse,
    MapRequest,
    MapResponse,
    ProductCrawlRequest,
    ProductCrawlResponse,
    ScrapeRequest,
    ScrapeResponse,
    ScreenshotRequest,
    ScreenshotResponse,
)

router = APIRouter(prefix="/v1/hosted", tags=["hosted"])

_HOSTED_ARTIFACT_FIELDS = {
    "manifest",
    "records_json",
    "records_jsonl",
    "source_pages_json",
    "blocked_pages_json",
    "validation_json",
    "report_md",
}


class HostedUsageSummary(BaseModel):
    """Non-secret hosted usage metadata returned to API callers."""

    tenant_id: str
    key_id: str
    credits_charged: int
    credit_type: str


class HostedScrapeResponse(BaseModel):
    """Hosted scrape response with hosted usage metadata."""

    success: bool
    hosted: HostedUsageSummary
    scrape: ScrapeResponse


class HostedCrawlResponse(BaseModel):
    """Hosted crawl response with hosted usage metadata."""

    success: bool
    hosted: HostedUsageSummary
    crawl: CrawlResponse


class HostedMapResponse(BaseModel):
    """Hosted map response with hosted usage metadata."""

    success: bool
    hosted: HostedUsageSummary
    map: MapResponse


class HostedProductsResponse(BaseModel):
    """Hosted product crawl response with hosted usage metadata."""

    success: bool
    hosted: HostedUsageSummary
    products: ProductCrawlResponse


class HostedScreenshotResponse(BaseModel):
    """Hosted screenshot response with hosted usage metadata."""

    success: bool
    hosted: HostedUsageSummary
    screenshot: ScreenshotResponse


class HostedRunResponse(BaseModel):
    """Hosted high-level run response with hosted usage metadata."""

    success: bool
    hosted: HostedUsageSummary
    run: RunResponse


class HostedAcceptedJobResponse(BaseModel):
    """Response returned when hosted work is queued for async execution."""

    success: bool = True
    accepted: bool = True
    job_id: str
    kind: str
    status: str
    job_url: str
    retry_after_seconds: int
    hosted: HostedUsageSummary


class HostedJobStatusResponse(BaseModel):
    """Pollable hosted job state and result."""

    success: bool
    job_id: str
    kind: str
    status: str
    retry_after_seconds: int
    hosted: HostedUsageSummary
    created_at: str
    started_at: str = ""
    finished_at: str = ""
    result: dict[str, Any] | None = None
    error: str = ""


class HostedAccountSummaryResponse(BaseModel):
    """Non-secret hosted account, plan, and usage balance summary."""

    tenant_id: str
    key_id: str
    plan: str
    account_status: str
    balance: HostedUsageBalance
    limits: HostedPlanLimits
    usage_summary: dict[str, object]
    purchase_summary: dict[str, object]
    links: dict[str, str]


class HostedBetaKeyRequest(BaseModel):
    """Hosted beta key generation request."""

    name: str = ""
    email: EmailStr
    key_name: str = "Hosted beta key"


class HostedBetaKeyResponse(BaseModel):
    """Hosted beta key registration response without raw secret material."""

    success: bool
    tenant_id: str
    key_id: str
    name: str
    email: str
    plan: str
    scopes: list[str]
    standard_credits_remaining: int
    browser_credits_remaining: int
    delivery_status: str
    warning: str


@router.get("/me", response_model=HostedAccountSummaryResponse)
async def hosted_me(
    authorization: str = Header(default=""),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
    payment_service: HostedPaymentProvisioningService = Depends(
        get_hosted_payment_provisioning_service
    ),
) -> HostedAccountSummaryResponse:
    """Return hosted account limits and remaining credits for a Bearer key."""
    raw_key = _bearer_token(authorization)
    auth = account_service.authenticate_key(raw_key, required_scope="runs:create")
    if not auth.allowed:
        raise HTTPException(status_code=403, detail=auth.reason)
    _enforce_rate_limit(rate_limiter, auth.key_id)
    tenant = account_service.get_tenant(auth.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=403, detail="Hosted account is not active.")
    return HostedAccountSummaryResponse(
        tenant_id=auth.tenant_id,
        key_id=auth.key_id,
        plan=tenant.plan.value,
        account_status=tenant.status.value,
        balance=account_service.get_balance(auth.tenant_id),
        limits=plan_limits(tenant.plan),
        usage_summary=_usage_summary(account_service, auth.tenant_id),
        purchase_summary=_purchase_summary(payment_service, auth.tenant_id),
        links=_hosted_account_links(),
    )


@router.get("/usage")
async def hosted_usage(
    limit: int = 100,
    authorization: str = Header(default=""),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
) -> dict[str, Any]:
    """Return recent hosted credit ledger entries for the Bearer key tenant."""
    auth = _hosted_auth_for_read(authorization, account_service, rate_limiter)
    entries = account_service.list_usage(auth.tenant_id, limit=limit)
    return {
        "total": len(entries),
        "usage": [entry.model_dump(mode="json") for entry in entries],
    }


@router.get("/purchases")
async def hosted_purchases(
    limit: int = 100,
    authorization: str = Header(default=""),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
    payment_service: HostedPaymentProvisioningService = Depends(
        get_hosted_payment_provisioning_service
    ),
) -> dict[str, Any]:
    """Return hosted checkout/package purchase records for the Bearer key tenant."""
    auth = _hosted_auth_for_read(authorization, account_service, rate_limiter)
    purchases = payment_service.payment_store.list_checkouts(
        tenant_id=auth.tenant_id,
        limit=limit,
    )
    return {
        "total": len(purchases),
        "purchases": [purchase.model_dump(mode="json") for purchase in purchases],
    }


def _usage_summary(
    account_service: HostedAccountService,
    tenant_id: str,
) -> dict[str, object]:
    """Return compact usage telemetry for the hosted account summary."""
    entries = account_service.list_usage(tenant_id, limit=500)
    standard_credits_used = sum(
        entry.credits for entry in entries if entry.credit_type == "standard"
    )
    browser_credits_used = sum(entry.credits for entry in entries if entry.credit_type == "browser")
    return {
        "total_events": len(entries),
        "standard_credits_used": standard_credits_used,
        "browser_credits_used": browser_credits_used,
        "usage_url": "/v1/hosted/usage",
    }


def _purchase_summary(
    payment_service: HostedPaymentProvisioningService,
    tenant_id: str,
) -> dict[str, object]:
    """Return compact purchase telemetry for the hosted account summary."""
    purchases = payment_service.payment_store.list_checkouts(tenant_id=tenant_id, limit=500)
    total_amount_cents = sum(purchase.amount_total_cents for purchase in purchases)
    last_purchase = purchases[0] if purchases else None
    return {
        "total_purchases": len(purchases),
        "total_amount_cents": total_amount_cents,
        "currency": last_purchase.currency if last_purchase is not None else "",
        "last_package_id": last_purchase.package_id if last_purchase is not None else "",
        "purchases_url": "/v1/hosted/purchases",
    }


def _hosted_account_links() -> dict[str, str]:
    """Return stable self-service links for hosted API callers."""
    return {
        "usage": "/v1/hosted/usage",
        "purchases": "/v1/hosted/purchases",
        "docs": "https://scout.chowmes.com/docs",
        "pricing": "https://scout.chowmes.com/pricing",
    }


@router.post(
    "/beta-key",
    response_model=HostedBetaKeyResponse,
    response_model_exclude_none=True,
)
async def hosted_beta_key(
    req: HostedBetaKeyRequest,
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    delivery_service: HostedApiKeyDeliveryService = Depends(get_hosted_key_delivery_service),
) -> HostedBetaKeyResponse:
    """Provision a hosted beta API key after email capture."""
    if not settings.hosted_beta_signup_enabled:
        raise HTTPException(
            status_code=503,
            detail="Hosted beta key generation is disabled.",
        )
    if not delivery_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="Hosted API key delivery is not configured.",
        )
    try:
        provisioned = account_service.provision_account(
            email=str(req.email),
            name=req.name,
            plan=HostedPlan.HOSTED_BETA_PASS,
            scopes=["runs:create"],
            key_name=req.key_name.strip() or "Hosted beta key",
        )
    except ValueError as exc:
        if "already exists" in str(exc):
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        raise
    delivery = delivery_service.deliver(
        HostedApiKeyDeliveryRequest(
            email=provisioned.tenant.email,
            name=provisioned.tenant.name,
            tenant_id=provisioned.tenant.tenant_id,
            key_id=provisioned.api_key.key_id,
            plan=provisioned.tenant.plan,
            raw_api_key=provisioned.raw_api_key,
            checkout_session_id="beta_signup",
        )
    )
    if not delivery.delivered:
        account_service.delete_account(provisioned.tenant.tenant_id)
        raise HTTPException(status_code=502, detail=delivery.reason)
    return HostedBetaKeyResponse(
        success=True,
        tenant_id=provisioned.tenant.tenant_id,
        key_id=provisioned.api_key.key_id,
        name=provisioned.tenant.name,
        email=str(provisioned.tenant.email),
        plan=provisioned.tenant.plan.value,
        scopes=provisioned.api_key.scopes,
        standard_credits_remaining=provisioned.balance.standard_credits_remaining,
        browser_credits_remaining=provisioned.balance.browser_credits_remaining,
        delivery_status=delivery.delivery_status,
        warning="Scout emailed the API key. It stores only a hash and cannot show the raw key again.",
    )


@router.post("/scrape", response_model=HostedScrapeResponse)
async def hosted_scrape(
    req: ScrapeRequest,
    authorization: str = Header(default=""),
    crawler: ScoutCrawler = Depends(get_crawler),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
    admission: AdmissionController = Depends(get_hosted_admission_controller),
    job_queue: HostedJobQueue = Depends(get_hosted_job_queue),
) -> HostedScrapeResponse | JSONResponse:
    """Run a hosted scrape after Bearer auth, URL safety, and credit admission."""
    raw_key = _bearer_token(authorization)
    auth = account_service.authenticate_key(raw_key, required_scope="runs:create")
    if not auth.allowed:
        raise HTTPException(status_code=403, detail=auth.reason)
    _enforce_hosted_url_safety(req.url)
    _enforce_rate_limit(rate_limiter, auth.key_id)
    if settings.hosted_async_first:
        return _queue_hosted_job(
            job_queue,
            kind="scrape",
            tenant_id=auth.tenant_id,
            key_id=auth.key_id,
            retry_after_seconds=settings.capacity_retry_after_seconds,
            work=lambda: _execute_hosted_scrape(req, raw_key, crawler, account_service),
        )
    try:
        async with admission.admit():
            return await _execute_hosted_scrape(req, raw_key, crawler, account_service)
    except AdmissionRejected as exc:
        return _queue_hosted_job(
            job_queue,
            kind="scrape",
            tenant_id=auth.tenant_id,
            key_id=auth.key_id,
            retry_after_seconds=exc.retry_after_seconds,
            work=lambda: _execute_hosted_scrape(req, raw_key, crawler, account_service),
        )


@router.post("/crawl", response_model=HostedCrawlResponse)
async def hosted_crawl(
    req: CrawlRequest,
    authorization: str = Header(default=""),
    crawler: ScoutCrawler = Depends(get_crawler),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
    admission: AdmissionController = Depends(get_hosted_admission_controller),
    job_queue: HostedJobQueue = Depends(get_hosted_job_queue),
) -> HostedCrawlResponse | JSONResponse:
    """Run a hosted crawl after Bearer auth, URL safety, rate, and credit checks."""
    raw_key = _bearer_token(authorization)
    auth = account_service.authenticate_key(raw_key, required_scope="runs:create")
    if not auth.allowed:
        raise HTTPException(status_code=403, detail=auth.reason)
    _enforce_hosted_url_safety(req.url)
    tenant = account_service.get_tenant(auth.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=403, detail="Hosted account is not active.")
    limits = plan_limits(tenant.plan)
    _enforce_crawl_page_limit(req.max_pages, limits)
    _enforce_standard_credit_preflight(account_service, auth.tenant_id, req.max_pages)
    _enforce_rate_limit(rate_limiter, auth.key_id)
    if settings.hosted_async_first:
        return _queue_hosted_job(
            job_queue,
            kind="crawl",
            tenant_id=auth.tenant_id,
            key_id=auth.key_id,
            retry_after_seconds=settings.capacity_retry_after_seconds,
            work=lambda: _execute_hosted_crawl(
                req,
                auth.tenant_id,
                auth.key_id,
                crawler,
                account_service,
            ),
        )

    try:
        async with admission.admit():
            return await _execute_hosted_crawl(
                req, auth.tenant_id, auth.key_id, crawler, account_service
            )
    except AdmissionRejected as exc:
        return _queue_hosted_job(
            job_queue,
            kind="crawl",
            tenant_id=auth.tenant_id,
            key_id=auth.key_id,
            retry_after_seconds=exc.retry_after_seconds,
            work=lambda: _execute_hosted_crawl(
                req,
                auth.tenant_id,
                auth.key_id,
                crawler,
                account_service,
            ),
        )


@router.post("/map", response_model=HostedMapResponse)
async def hosted_map(
    req: MapRequest,
    authorization: str = Header(default=""),
    crawler: ScoutCrawler = Depends(get_crawler),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
    admission: AdmissionController = Depends(get_hosted_admission_controller),
    job_queue: HostedJobQueue = Depends(get_hosted_job_queue),
) -> HostedMapResponse | JSONResponse:
    """Run hosted URL discovery after Bearer auth, URL safety, rate, and credits."""
    raw_key = _bearer_token(authorization)
    auth = account_service.authenticate_key(raw_key, required_scope="runs:create")
    if not auth.allowed:
        raise HTTPException(status_code=403, detail=auth.reason)
    _enforce_hosted_url_safety(req.url)
    tenant = account_service.get_tenant(auth.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=403, detail="Hosted account is not active.")
    limits = plan_limits(tenant.plan)
    _enforce_map_page_limit(req.max_pages, limits)
    _enforce_standard_credit_preflight(account_service, auth.tenant_id, req.max_pages)
    _enforce_rate_limit(rate_limiter, auth.key_id)
    if settings.hosted_async_first:
        return _queue_hosted_job(
            job_queue,
            kind="map",
            tenant_id=auth.tenant_id,
            key_id=auth.key_id,
            retry_after_seconds=settings.capacity_retry_after_seconds,
            work=lambda: _execute_hosted_map(
                req,
                auth.tenant_id,
                auth.key_id,
                crawler,
                account_service,
            ),
        )

    try:
        async with admission.admit():
            return await _execute_hosted_map(
                req, auth.tenant_id, auth.key_id, crawler, account_service
            )
    except AdmissionRejected as exc:
        return _queue_hosted_job(
            job_queue,
            kind="map",
            tenant_id=auth.tenant_id,
            key_id=auth.key_id,
            retry_after_seconds=exc.retry_after_seconds,
            work=lambda: _execute_hosted_map(
                req,
                auth.tenant_id,
                auth.key_id,
                crawler,
                account_service,
            ),
        )


@router.post("/products", response_model=HostedProductsResponse)
async def hosted_products(
    req: ProductCrawlRequest,
    authorization: str = Header(default=""),
    crawler: ScoutCrawler = Depends(get_crawler),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
    admission: AdmissionController = Depends(get_hosted_admission_controller),
    job_queue: HostedJobQueue = Depends(get_hosted_job_queue),
) -> HostedProductsResponse | JSONResponse:
    """Run hosted product extraction after auth, URL safety, rate, and credit checks."""
    raw_key = _bearer_token(authorization)
    auth = account_service.authenticate_key(raw_key, required_scope="runs:create")
    if not auth.allowed:
        raise HTTPException(status_code=403, detail=auth.reason)
    target_url = _hosted_product_target_url(req)
    _enforce_hosted_url_safety(target_url)
    tenant = account_service.get_tenant(auth.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=403, detail="Hosted account is not active.")
    limits = plan_limits(tenant.plan)
    _enforce_product_limit(req.max_products, limits)
    _enforce_standard_credit_preflight(account_service, auth.tenant_id, req.max_products)
    _enforce_rate_limit(rate_limiter, auth.key_id)
    if settings.hosted_async_first:
        return _queue_hosted_job(
            job_queue,
            kind="products",
            tenant_id=auth.tenant_id,
            key_id=auth.key_id,
            retry_after_seconds=settings.capacity_retry_after_seconds,
            work=lambda: _execute_hosted_products(
                req,
                auth.tenant_id,
                auth.key_id,
                crawler,
                account_service,
            ),
        )

    try:
        async with admission.admit():
            return await _execute_hosted_products(
                req,
                auth.tenant_id,
                auth.key_id,
                crawler,
                account_service,
            )
    except AdmissionRejected as exc:
        return _queue_hosted_job(
            job_queue,
            kind="products",
            tenant_id=auth.tenant_id,
            key_id=auth.key_id,
            retry_after_seconds=exc.retry_after_seconds,
            work=lambda: _execute_hosted_products(
                req,
                auth.tenant_id,
                auth.key_id,
                crawler,
                account_service,
            ),
        )


@router.post("/screenshot", response_model=HostedScreenshotResponse)
async def hosted_screenshot(
    req: ScreenshotRequest,
    authorization: str = Header(default=""),
    crawler: ScoutCrawler = Depends(get_crawler),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
    admission: AdmissionController = Depends(get_hosted_admission_controller),
    job_queue: HostedJobQueue = Depends(get_hosted_job_queue),
) -> HostedScreenshotResponse | JSONResponse:
    """Run hosted screenshot capture after auth, URL safety, rate, and credit checks."""
    raw_key = _bearer_token(authorization)
    auth = account_service.authenticate_key(raw_key, required_scope="runs:create")
    if not auth.allowed:
        raise HTTPException(status_code=403, detail=auth.reason)
    _enforce_hosted_url_safety(req.url)
    _enforce_standard_credit_preflight(
        account_service,
        auth.tenant_id,
        HostedAction.SCREENSHOT.credit_cost,
    )
    _enforce_rate_limit(rate_limiter, auth.key_id)
    if settings.hosted_async_first:
        return _queue_hosted_job(
            job_queue,
            kind="screenshot",
            tenant_id=auth.tenant_id,
            key_id=auth.key_id,
            retry_after_seconds=settings.capacity_retry_after_seconds,
            work=lambda: _execute_hosted_screenshot(req, raw_key, crawler, account_service),
        )

    try:
        async with admission.admit():
            return await _execute_hosted_screenshot(req, raw_key, crawler, account_service)
    except AdmissionRejected as exc:
        return _queue_hosted_job(
            job_queue,
            kind="screenshot",
            tenant_id=auth.tenant_id,
            key_id=auth.key_id,
            retry_after_seconds=exc.retry_after_seconds,
            work=lambda: _execute_hosted_screenshot(req, raw_key, crawler, account_service),
        )


@router.post("/run/{use_case}", response_model=HostedRunResponse)
async def hosted_run(
    use_case: str,
    req: RunRequest,
    authorization: str = Header(default=""),
    crawler: ScoutCrawler | None = Depends(get_crawler_optional),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
    admission: AdmissionController = Depends(get_hosted_admission_controller),
    job_queue: HostedJobQueue = Depends(get_hosted_job_queue),
) -> HostedRunResponse | JSONResponse:
    """Run a hosted high-level Scout use case after hosted admission checks."""
    raw_key = _bearer_token(authorization)
    auth = account_service.authenticate_key(raw_key, required_scope="runs:create")
    if not auth.allowed:
        raise HTTPException(status_code=403, detail=auth.reason)
    _enforce_hosted_run_url_safety(req)
    tenant = account_service.get_tenant(auth.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=403, detail="Hosted account is not active.")
    limits = plan_limits(tenant.plan)
    _enforce_run_record_limit(req.max_records, limits)
    _enforce_standard_credit_preflight(account_service, auth.tenant_id, req.max_records)
    _enforce_rate_limit(rate_limiter, auth.key_id)

    hosted_req = req.model_copy(
        update={
            "use_case": use_case,
            "output_dir": resolve_run_output_dir(
                use_case=f"hosted-{auth.tenant_id}-{use_case}",
                query=req.query,
                output_dir="",
                workdir=settings.scout_workdir,
            ),
        }
    )
    if settings.hosted_async_first:
        return _queue_hosted_job(
            job_queue,
            kind=f"run:{use_case}",
            tenant_id=auth.tenant_id,
            key_id=auth.key_id,
            retry_after_seconds=settings.capacity_retry_after_seconds,
            work=lambda: _execute_hosted_run(
                hosted_req,
                auth.tenant_id,
                auth.key_id,
                account_service,
                crawler,
            ),
        )
    try:
        async with admission.admit():
            return await _execute_hosted_run(
                hosted_req, auth.tenant_id, auth.key_id, account_service, crawler
            )
    except AdmissionRejected as exc:
        return _queue_hosted_job(
            job_queue,
            kind=f"run:{use_case}",
            tenant_id=auth.tenant_id,
            key_id=auth.key_id,
            retry_after_seconds=exc.retry_after_seconds,
            work=lambda: _execute_hosted_run(
                hosted_req,
                auth.tenant_id,
                auth.key_id,
                account_service,
                crawler,
            ),
        )


@router.get("/jobs/{job_id}", response_model=HostedJobStatusResponse)
async def hosted_job_status(
    job_id: str,
    authorization: str = Header(default=""),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
    job_queue: HostedJobQueue = Depends(get_hosted_job_queue),
) -> HostedJobStatusResponse:
    """Return queued hosted job status/result for the owning tenant."""
    auth = _hosted_auth_for_read(authorization, account_service, rate_limiter)
    job = job_queue.get(job_id)
    if job is None or job.tenant_id != auth.tenant_id:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return HostedJobStatusResponse(
        success=job.status == "complete",
        job_id=job.job_id,
        kind=job.kind,
        status=job.status,
        retry_after_seconds=job.retry_after_seconds,
        hosted=HostedUsageSummary(
            tenant_id=job.tenant_id,
            key_id=job.key_id,
            credits_charged=0,
            credit_type=HostedAction.CRAWL_PAGE.credit_type,
        ),
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        result=job.result,
        error=job.error,
    )


@router.get("/runs")
async def hosted_run_list(
    limit: int = 50,
    authorization: str = Header(default=""),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
) -> dict[str, Any]:
    """Return recent hosted runs owned by the Bearer key."""
    auth = _hosted_auth_for_read(authorization, account_service, rate_limiter)
    runs = await list_runs(tenant_id=auth.tenant_id, limit=limit)
    items = [_hosted_run_list_item(run) for run in runs]
    return {"total": len(items), "runs": items}


@router.get("/runs/{run_id}")
async def hosted_run_summary(
    run_id: str,
    authorization: str = Header(default=""),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
) -> dict[str, Any]:
    """Return a hosted run summary if the Bearer key owns the hosted run."""
    auth = _hosted_auth_for_read(authorization, account_service, rate_limiter)
    run = await _require_hosted_run(run_id, auth.tenant_id)
    return run.model_dump(mode="json")


@router.get("/runs/{run_id}/records")
async def hosted_run_records(
    run_id: str,
    authorization: str = Header(default=""),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
) -> dict[str, Any]:
    """Return records for a hosted run if the Bearer key owns it."""
    auth = _hosted_auth_for_read(authorization, account_service, rate_limiter)
    run = await _require_hosted_run(run_id, auth.tenant_id)
    records = _read_json_list(_hosted_artifact_path(run, "records_json"))
    return {"run_id": run_id, "total": len(records), "records": records}


@router.get("/runs/{run_id}/artifacts")
async def hosted_run_artifacts(
    run_id: str,
    authorization: str = Header(default=""),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
) -> dict[str, Any]:
    """Return artifact paths and private download URLs for an owned hosted run."""
    auth = _hosted_auth_for_read(authorization, account_service, rate_limiter)
    run = await _require_hosted_run(run_id, auth.tenant_id)
    return {
        "run_id": run_id,
        "output_dir": run.output_dir,
        "artifacts": run.artifacts.model_dump(mode="json"),
        "download_urls": _hosted_artifact_download_urls(run),
    }


@router.get("/runs/{run_id}/artifacts/{artifact_name}/download")
async def hosted_run_artifact_download(
    run_id: str,
    artifact_name: str,
    authorization: str = Header(default=""),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
) -> FileResponse:
    """Download a single artifact for a hosted run owned by the Bearer key."""
    auth = _hosted_auth_for_read(authorization, account_service, rate_limiter)
    run = await _require_hosted_run(run_id, auth.tenant_id)
    path = _hosted_artifact_path(run, artifact_name)
    return FileResponse(path, media_type=_artifact_media_type(path), filename=path.name)


def _bearer_token(authorization: str) -> str:
    """Extract a Bearer token or reject the hosted request."""
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization[len(prefix) :].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    return token


async def _execute_hosted_scrape(
    req: ScrapeRequest,
    raw_key: str,
    crawler: ScoutCrawler,
    account_service: HostedAccountService,
) -> HostedScrapeResponse:
    """Run hosted scrape and debit one scrape credit when execution starts."""
    usage = account_service.consume_action(
        raw_key,
        HostedAction.SCRAPE,
        required_scope="runs:create",
    )
    if not usage.allowed:
        raise HTTPException(status_code=403, detail=usage.reason)
    scrape_response = await crawler.scrape(req)
    return HostedScrapeResponse(
        success=scrape_response.success,
        hosted=HostedUsageSummary(
            tenant_id=usage.tenant_id,
            key_id=usage.key_id,
            credits_charged=usage.usage.cost if usage.usage else 0,
            credit_type=usage.usage.credit_type if usage.usage else "",
        ),
        scrape=scrape_response,
    )


async def _execute_hosted_crawl(
    req: CrawlRequest,
    tenant_id: str,
    key_id: str,
    crawler: ScoutCrawler,
    account_service: HostedAccountService,
) -> HostedCrawlResponse:
    """Run hosted crawl and debit returned page credits."""
    crawl_response = await crawler.crawl(req)
    pages_charged = _hosted_crawl_pages_charged(crawl_response, req.max_pages)
    _debit_standard_credits(
        account_service,
        tenant_id=tenant_id,
        key_id=key_id,
        action=HostedAction.CRAWL_PAGE,
        credits=pages_charged,
    )
    return HostedCrawlResponse(
        success=crawl_response.success,
        hosted=HostedUsageSummary(
            tenant_id=tenant_id,
            key_id=key_id,
            credits_charged=pages_charged,
            credit_type=HostedAction.CRAWL_PAGE.credit_type,
        ),
        crawl=crawl_response,
    )


async def _execute_hosted_map(
    req: MapRequest,
    tenant_id: str,
    key_id: str,
    crawler: ScoutCrawler,
    account_service: HostedAccountService,
) -> HostedMapResponse:
    """Run hosted URL discovery and debit returned URL credits."""
    map_response = await crawler.map_urls(req)
    pages_charged = _hosted_map_pages_charged(map_response, req.max_pages)
    _debit_standard_credits(
        account_service,
        tenant_id=tenant_id,
        key_id=key_id,
        action=HostedAction.CRAWL_PAGE,
        credits=pages_charged,
    )
    return HostedMapResponse(
        success=map_response.success,
        hosted=HostedUsageSummary(
            tenant_id=tenant_id,
            key_id=key_id,
            credits_charged=pages_charged,
            credit_type=HostedAction.CRAWL_PAGE.credit_type,
        ),
        map=map_response,
    )


async def _execute_hosted_products(
    req: ProductCrawlRequest,
    tenant_id: str,
    key_id: str,
    crawler: ScoutCrawler,
    account_service: HostedAccountService,
) -> HostedProductsResponse:
    """Run hosted product extraction and debit returned record credits."""
    products_response = await crawler.products(req)
    records_charged = _hosted_product_records_charged(products_response, req.max_products)
    _debit_standard_credits(
        account_service,
        tenant_id=tenant_id,
        key_id=key_id,
        action=HostedAction.CRAWL_PAGE,
        credits=records_charged,
    )
    return HostedProductsResponse(
        success=products_response.success,
        hosted=HostedUsageSummary(
            tenant_id=tenant_id,
            key_id=key_id,
            credits_charged=records_charged,
            credit_type=HostedAction.CRAWL_PAGE.credit_type,
        ),
        products=products_response,
    )


async def _execute_hosted_screenshot(
    req: ScreenshotRequest,
    raw_key: str,
    crawler: ScoutCrawler,
    account_service: HostedAccountService,
) -> HostedScreenshotResponse:
    """Run hosted screenshot capture and debit screenshot credits when execution starts."""
    usage = account_service.consume_action(
        raw_key,
        HostedAction.SCREENSHOT,
        required_scope="runs:create",
    )
    if not usage.allowed:
        raise HTTPException(status_code=403, detail=usage.reason)
    screenshot_response = await crawler.screenshot(req)
    return HostedScreenshotResponse(
        success=screenshot_response.success,
        hosted=HostedUsageSummary(
            tenant_id=usage.tenant_id,
            key_id=usage.key_id,
            credits_charged=usage.usage.cost if usage.usage else 0,
            credit_type=usage.usage.credit_type if usage.usage else "",
        ),
        screenshot=screenshot_response,
    )


async def _execute_hosted_run(
    hosted_req: RunRequest,
    tenant_id: str,
    key_id: str,
    account_service: HostedAccountService,
    crawler: ScoutCrawler | None,
) -> HostedRunResponse:
    """Run a hosted high-level use case, persist artifacts, and debit records."""
    run_response = await run_use_case(hosted_req, crawler)
    if run_response.manifest is not None:
        await remember_run(run_response.manifest, tenant_id=tenant_id, key_id=key_id)
    records_charged = _hosted_run_records_charged(run_response, hosted_req.max_records)
    _debit_standard_credits(
        account_service,
        tenant_id=tenant_id,
        key_id=key_id,
        action=HostedAction.CRAWL_PAGE,
        credits=records_charged,
    )
    return HostedRunResponse(
        success=run_response.success,
        hosted=HostedUsageSummary(
            tenant_id=tenant_id,
            key_id=key_id,
            credits_charged=records_charged,
            credit_type=HostedAction.CRAWL_PAGE.credit_type,
        ),
        run=run_response,
    )


def _queue_hosted_job(
    queue: HostedJobQueue,
    *,
    kind: str,
    tenant_id: str,
    key_id: str,
    retry_after_seconds: int,
    work,
) -> JSONResponse:
    """Queue hosted work and return a 202 response with a poll URL."""
    if queue.worker_count == 0:
        raise _capacity_exception(
            "Hosted async queue has no workers; retry shortly.",
            HostedQueueFull(queue.retry_after_seconds),
        )
    try:
        job = queue.enqueue(
            kind=kind,
            tenant_id=tenant_id,
            key_id=key_id,
            retry_after_seconds=retry_after_seconds,
            work=work,
        )
    except HostedQueueFull as exc:
        raise _capacity_exception("Hosted async queue is full; retry shortly.", exc) from exc
    response = HostedAcceptedJobResponse(
        job_id=job.job_id,
        kind=job.kind,
        status=job.status,
        job_url=f"/v1/hosted/jobs/{job.job_id}",
        retry_after_seconds=job.retry_after_seconds,
        hosted=HostedUsageSummary(
            tenant_id=tenant_id,
            key_id=key_id,
            credits_charged=0,
            credit_type=HostedAction.CRAWL_PAGE.credit_type,
        ),
    )
    return JSONResponse(
        status_code=202,
        content=response.model_dump(mode="json"),
        headers={"Retry-After": str(job.retry_after_seconds)},
    )


def _enforce_hosted_url_safety(url: str) -> None:
    """Reject unsafe hosted fetch URLs before crawler work starts."""
    url_safety = validate_hosted_url_with_dns(url)
    if not url_safety.allowed:
        raise HTTPException(status_code=403, detail=url_safety.reason)


def _enforce_hosted_run_url_safety(req: RunRequest) -> None:
    """Reject unsafe URL-bearing fields from high-level hosted run requests."""
    values: list[str] = []
    if req.url:
        values.append(req.url)
    values.extend(req.targets)
    values.extend(req.job_urls)
    url_safety = validate_hosted_url_fields(values)
    if not url_safety.allowed:
        raise HTTPException(status_code=403, detail=url_safety.reason)


def _hosted_auth_for_read(
    authorization: str,
    account_service: HostedAccountService,
    rate_limiter: HostedRateLimiter,
):
    """Authenticate hosted read requests and apply per-key throttling."""
    raw_key = _bearer_token(authorization)
    auth = account_service.authenticate_key(raw_key, required_scope="runs:create")
    if not auth.allowed:
        raise HTTPException(status_code=403, detail=auth.reason)
    _enforce_rate_limit(rate_limiter, auth.key_id)
    return auth


async def _require_hosted_run(run_id: str, tenant_id: str) -> StoredRun:
    """Return a run only if it belongs to the hosted tenant."""
    run = await get_run(run_id)
    if run is None or not _run_belongs_to_tenant(run, tenant_id):
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return run


def _run_belongs_to_tenant(run: StoredRun, tenant_id: str) -> bool:
    """Check hosted run ownership using persisted tenant metadata."""
    return run.tenant_id == tenant_id


def _hosted_run_list_item(run: StoredRun) -> dict[str, Any]:
    """Return dashboard-safe hosted run metadata without local filesystem paths."""
    return {
        "run_id": run.run_id,
        "use_case": run.use_case,
        "query": run.query,
        "status": run.status,
        "summary_url": f"/v1/hosted/runs/{run.run_id}",
        "records_url": f"/v1/hosted/runs/{run.run_id}/records",
        "artifacts_url": f"/v1/hosted/runs/{run.run_id}/artifacts",
    }


def _read_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact not found: {path}")
    data = json.loads(path.read_text())
    return data if isinstance(data, list) else []


def _hosted_artifact_download_urls(run: StoredRun) -> dict[str, str]:
    """Return relative authenticated download URLs for artifacts that exist."""
    urls: dict[str, str] = {}
    for artifact_name in _HOSTED_ARTIFACT_FIELDS:
        value = getattr(run.artifacts, artifact_name)
        if not value:
            continue
        urls[artifact_name] = f"/v1/hosted/runs/{run.run_id}/artifacts/{artifact_name}/download"
    return urls


def _hosted_artifact_path(run: StoredRun, artifact_name: str) -> Path:
    """Resolve an artifact path only when it is a known file inside the run output dir."""
    if artifact_name not in _HOSTED_ARTIFACT_FIELDS:
        raise HTTPException(status_code=404, detail=f"Artifact not found: {artifact_name}")
    value = getattr(run.artifacts, artifact_name)
    if not value:
        raise HTTPException(status_code=404, detail=f"Artifact not found: {artifact_name}")
    path = Path(value).resolve()
    output_dir = Path(run.output_dir).resolve()
    try:
        path.relative_to(output_dir)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Artifact not found: {artifact_name}",
        ) from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Artifact not found: {artifact_name}")
    return path


def _artifact_media_type(path: Path) -> str:
    if path.suffix == ".json":
        return "application/json"
    if path.suffix == ".jsonl":
        return "application/x-ndjson"
    if path.suffix == ".md":
        return "text/markdown"
    return "application/octet-stream"


def _enforce_rate_limit(rate_limiter: HostedRateLimiter, key_id: str) -> None:
    """Reject hosted requests that exceed the configured per-key rate limit."""
    decision = rate_limiter.admit(key_id)
    if decision.allowed:
        return
    raise HTTPException(
        status_code=429,
        detail=decision.reason,
        headers={"Retry-After": str(decision.retry_after_seconds)},
    )


def _capacity_exception(detail: str, exc: AdmissionRejected | HostedQueueFull) -> HTTPException:
    """Return a retryable overload response for expensive hosted work."""
    return HTTPException(
        status_code=429,
        detail=detail,
        headers={"Retry-After": str(exc.retry_after_seconds)},
    )


def _enforce_crawl_page_limit(max_pages: int, limits: HostedPlanLimits) -> None:
    """Reject hosted crawls that exceed plan page limits."""
    if max_pages < 1:
        raise HTTPException(status_code=403, detail="Hosted crawls require at least 1 page.")
    if max_pages > limits.max_pages_per_run:
        raise HTTPException(
            status_code=403,
            detail=f"Plan allows at most {limits.max_pages_per_run} pages per crawl.",
        )


def _enforce_map_page_limit(max_pages: int, limits: HostedPlanLimits) -> None:
    """Reject hosted maps that exceed plan URL limits."""
    if max_pages < 1:
        raise HTTPException(status_code=403, detail="Hosted maps require at least 1 URL.")
    if max_pages > limits.max_pages_per_run:
        raise HTTPException(
            status_code=403,
            detail=f"Plan allows at most {limits.max_pages_per_run} URLs per map.",
        )


def _enforce_standard_credit_preflight(
    account_service: HostedAccountService,
    tenant_id: str,
    needed_credits: int,
) -> None:
    """Require enough standard credits before accepting hosted work."""
    balance = account_service.get_balance(tenant_id)
    remaining = balance.standard_credits_remaining
    if remaining < needed_credits:
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient standard credits: need {needed_credits}, have {remaining}.",
        )


def _hosted_crawl_pages_charged(response: CrawlResponse, requested_max_pages: int) -> int:
    """Return page-credit charge for a crawl response, capped by requested max_pages."""
    observed_pages = max(response.total_pages, len(response.pages))
    return min(observed_pages, requested_max_pages)


def _hosted_map_pages_charged(response: MapResponse, requested_max_pages: int) -> int:
    """Return URL-credit charge for a map response, capped by requested max_pages."""
    observed_pages = max(response.total, len(response.urls))
    return min(observed_pages, requested_max_pages)


def _hosted_product_target_url(req: ProductCrawlRequest) -> str:
    """Return the URL used for hosted product URL safety checks."""
    target = req.start_url or req.site
    if not target:
        raise HTTPException(status_code=403, detail="Hosted products require site or start_url.")
    if target.startswith(("http://", "https://")):
        return target
    return f"https://{target}"


def _enforce_product_limit(max_products: int, limits: HostedPlanLimits) -> None:
    """Reject hosted product crawls that exceed plan limits."""
    if max_products < 1:
        raise HTTPException(
            status_code=403,
            detail="Hosted product requests require at least 1 product.",
        )
    if max_products > limits.max_pages_per_run:
        raise HTTPException(
            status_code=403,
            detail=f"Plan allows at most {limits.max_pages_per_run} products per request.",
        )


def _enforce_run_record_limit(max_records: int, limits: HostedPlanLimits) -> None:
    """Reject hosted high-level runs that exceed plan record limits."""
    if max_records < 1:
        raise HTTPException(
            status_code=403,
            detail="Hosted runs require at least 1 record.",
        )
    if max_records > limits.max_pages_per_run:
        raise HTTPException(
            status_code=403,
            detail=f"Plan allows at most {limits.max_pages_per_run} records per hosted run.",
        )


def _hosted_product_records_charged(
    response: ProductCrawlResponse,
    requested_max_products: int,
) -> int:
    """Return product-credit charge, capped by requested max_products."""
    observed_records = max(response.total_records, len(response.records))
    return min(observed_records, requested_max_products)


def _hosted_run_records_charged(response: RunResponse, requested_max_records: int) -> int:
    """Return high-level run credit charge, capped by requested max_records."""
    return min(response.total_records, requested_max_records)


def _debit_standard_credits(
    account_service: HostedAccountService,
    *,
    tenant_id: str,
    key_id: str,
    action: HostedAction,
    credits: int,
) -> None:
    """Debit standard credits after hosted crawl work is complete."""
    if credits <= 0:
        return
    account_service.debit_standard_credits(
        tenant_id=tenant_id,
        key_id=key_id,
        action=action,
        credits=credits,
    )
