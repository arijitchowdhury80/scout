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
from scout.core.types import ScrapeRequest, ScrapeResponse

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
