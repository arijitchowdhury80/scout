"""Hosted API routes protected by Scout hosted Bearer keys."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from scout.api.deps import get_crawler, get_hosted_account_service, get_hosted_rate_limiter
from scout.core.crawler import ScoutCrawler
from scout.core.platform.account_service import HostedAccountService
from scout.core.platform.hosted import (
    HostedAction,
    HostedPlanLimits,
    HostedUsageBalance,
    plan_limits,
)
from scout.core.platform.hosted_rate_limit import HostedRateLimiter
from scout.core.platform.url_safety import validate_hosted_url
from scout.core.types import CrawlRequest, CrawlResponse, ScrapeRequest, ScrapeResponse

router = APIRouter(prefix="/v1/hosted", tags=["hosted"])


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


class HostedAccountSummaryResponse(BaseModel):
    """Non-secret hosted account, plan, and usage balance summary."""

    tenant_id: str
    key_id: str
    plan: str
    account_status: str
    balance: HostedUsageBalance
    limits: HostedPlanLimits


@router.get("/me", response_model=HostedAccountSummaryResponse)
async def hosted_me(
    authorization: str = Header(default=""),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
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
    )


@router.post("/scrape", response_model=HostedScrapeResponse)
async def hosted_scrape(
    req: ScrapeRequest,
    authorization: str = Header(default=""),
    crawler: ScoutCrawler = Depends(get_crawler),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
) -> HostedScrapeResponse:
    """Run a hosted scrape after Bearer auth, URL safety, and credit admission."""
    raw_key = _bearer_token(authorization)
    auth = account_service.authenticate_key(raw_key, required_scope="runs:create")
    if not auth.allowed:
        raise HTTPException(status_code=403, detail=auth.reason)
    url_safety = validate_hosted_url(req.url)
    if not url_safety.allowed:
        raise HTTPException(status_code=403, detail=url_safety.reason)
    _enforce_rate_limit(rate_limiter, auth.key_id)
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


@router.post("/crawl", response_model=HostedCrawlResponse)
async def hosted_crawl(
    req: CrawlRequest,
    authorization: str = Header(default=""),
    crawler: ScoutCrawler = Depends(get_crawler),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    rate_limiter: HostedRateLimiter = Depends(get_hosted_rate_limiter),
) -> HostedCrawlResponse:
    """Run a hosted crawl after Bearer auth, URL safety, rate, and credit checks."""
    raw_key = _bearer_token(authorization)
    auth = account_service.authenticate_key(raw_key, required_scope="runs:create")
    if not auth.allowed:
        raise HTTPException(status_code=403, detail=auth.reason)
    url_safety = validate_hosted_url(req.url)
    if not url_safety.allowed:
        raise HTTPException(status_code=403, detail=url_safety.reason)
    tenant = account_service.get_tenant(auth.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=403, detail="Hosted account is not active.")
    limits = plan_limits(tenant.plan)
    _enforce_crawl_page_limit(req.max_pages, limits)
    _enforce_crawl_credit_preflight(account_service, auth.tenant_id, req.max_pages)
    _enforce_rate_limit(rate_limiter, auth.key_id)

    crawl_response = await crawler.crawl(req)
    pages_charged = _hosted_crawl_pages_charged(crawl_response, req.max_pages)
    _debit_standard_credits(account_service, auth.tenant_id, pages_charged)
    return HostedCrawlResponse(
        success=crawl_response.success,
        hosted=HostedUsageSummary(
            tenant_id=auth.tenant_id,
            key_id=auth.key_id,
            credits_charged=pages_charged,
            credit_type=HostedAction.CRAWL_PAGE.credit_type,
        ),
        crawl=crawl_response,
    )


def _bearer_token(authorization: str) -> str:
    """Extract a Bearer token or reject the hosted request."""
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization[len(prefix) :].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    return token


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


def _enforce_crawl_page_limit(max_pages: int, limits: HostedPlanLimits) -> None:
    """Reject hosted crawls that exceed plan page limits."""
    if max_pages < 1:
        raise HTTPException(status_code=403, detail="Hosted crawls require at least 1 page.")
    if max_pages > limits.max_pages_per_run:
        raise HTTPException(
            status_code=403,
            detail=f"Plan allows at most {limits.max_pages_per_run} pages per crawl.",
        )


def _enforce_crawl_credit_preflight(
    account_service: HostedAccountService,
    tenant_id: str,
    max_pages: int,
) -> None:
    """Require enough standard credits for the requested hosted crawl size."""
    balance = account_service.get_balance(tenant_id)
    remaining = balance.standard_credits_remaining
    if remaining < max_pages:
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient standard credits: need {max_pages}, have {remaining}.",
        )


def _hosted_crawl_pages_charged(response: CrawlResponse, requested_max_pages: int) -> int:
    """Return page-credit charge for a crawl response, capped by requested max_pages."""
    observed_pages = max(response.total_pages, len(response.pages))
    return min(observed_pages, requested_max_pages)


def _debit_standard_credits(
    account_service: HostedAccountService,
    tenant_id: str,
    credits: int,
) -> None:
    """Debit standard credits after hosted crawl work is complete."""
    if credits <= 0:
        return
    balance = account_service.get_balance(tenant_id)
    account_service.set_balance(
        tenant_id,
        standard_credits=balance.standard_credits_remaining - credits,
        browser_credits=balance.browser_credits_remaining,
    )
