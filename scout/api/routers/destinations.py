"""Hosted Destinations endpoint — push run records to any connector.

Public-facing framing: "Exports + Destinations — push to your search index,
warehouse, or webhook." This is a general-purpose connector surface; Algolia
is one destination among several (webhook today, elastic/s3/bigquery later
via scout.core.platform.destinations.register_destination), never the
headline.

Wired into scout/api/main.py via app.include_router(destinations.router).
Path is under /v1/hosted/ so AuthMiddleware passes it through by prefix;
this router does its own Bearer-token auth via HostedAccountService.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field, ValidationError, model_validator

from scout.api.deps import get_hosted_account_service
from scout.core.platform.account_service import (
    HostedAccountService,
    HostedUsageLedgerEntry,
)
from scout.core.platform.destinations import (
    AlgoliaDestination,
    AlgoliaDestinationConfig,
    Destination,
    DestinationResult,
    WebhookDestination,
    WebhookDestinationConfig,
    get_destination,
    list_destinations,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/v1/hosted/destinations", tags=["destinations"])

# Credit cost policy for this endpoint: 1 standard credit per record pushed,
# matching the pricing model's "1 credit = 1 scrape / crawled page / product
# / record" rule (docs/product/pricing-model-2026-07-06.md).
_CREDIT_TYPE = "standard"
_CREDITS_PER_RECORD = 1


class DestinationSendRequest(BaseModel):
    """Request to push records to a named destination connector."""

    destination: str = Field(min_length=1)
    config: dict[str, Any] = Field(default_factory=dict)
    records: list[dict[str, Any]] = Field(default_factory=list)
    run_id: str = ""

    @model_validator(mode="after")
    def _require_records_or_run_id(self) -> "DestinationSendRequest":
        if not self.records and not self.run_id:
            raise ValueError("Provide either records or run_id.")
        return self


class DestinationHostedUsageSummary(BaseModel):
    """Non-secret hosted usage metadata returned alongside the push result."""

    tenant_id: str
    key_id: str
    credits_charged: int
    credit_type: str


class DestinationSendResponse(BaseModel):
    """Response for POST /v1/hosted/destinations/send."""

    success: bool
    hosted: DestinationHostedUsageSummary
    result: DestinationResult


@router.get("/")
async def list_available_destinations() -> dict[str, list[str]]:
    """Return the names of all registered destination connectors."""
    return {"destinations": list_destinations()}


@router.post("/send", response_model=DestinationSendResponse)
async def send_to_destination(
    req: DestinationSendRequest,
    authorization: str = Header(default=""),
    account_service: HostedAccountService = Depends(get_hosted_account_service),
) -> DestinationSendResponse:
    """Push records to a destination connector after Bearer auth + credit debit."""
    raw_key = _bearer_token(authorization)
    auth = account_service.authenticate_key(raw_key, required_scope="runs:create")
    if not auth.allowed:
        raise HTTPException(status_code=403, detail=auth.reason)

    if req.destination not in list_destinations():
        raise HTTPException(
            status_code=400,
            detail=f"Unknown destination: {req.destination}. Available: {list_destinations()}",
        )

    records = await _resolve_records(req, auth.tenant_id)

    # Validate connector config before spending any credits — a bad config
    # should never debit the tenant.
    try:
        _validate_config(req.destination, req.config)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    cost = len(records) * _CREDITS_PER_RECORD
    if cost:
        balance = _debit_credits(account_service, auth.tenant_id, auth.key_id, cost)
        if balance is None:
            raise HTTPException(
                status_code=402,
                detail=(
                    f"Insufficient {_CREDIT_TYPE} credits: need {cost} to push "
                    f"{len(records)} record(s)."
                ),
            )

    destination = _build_destination(req.destination, req.config)
    result = await destination.send(records)

    return DestinationSendResponse(
        success=result.success,
        hosted=DestinationHostedUsageSummary(
            tenant_id=auth.tenant_id,
            key_id=auth.key_id,
            credits_charged=cost,
            credit_type=_CREDIT_TYPE,
        ),
        result=result,
    )


def _validate_config(name: str, config: dict[str, Any]) -> None:
    """Validate connector config eagerly so bad requests never debit credits."""
    if name == "webhook":
        WebhookDestinationConfig(**config)
    elif name == "algolia":
        AlgoliaDestinationConfig(**config)
    else:
        # Future connectors (elastic, s3, bigquery, ...) validate themselves
        # via the registry's factory + their own Pydantic config model.
        get_destination(name, config)


def _build_destination(name: str, config: dict[str, Any]) -> Destination:
    """Build the destination connector.

    webhook/algolia go through the classes imported directly into this
    module (rather than the registry) so tests can patch WebhookDestination
    / AlgoliaDestination at this module's import site. Anything else falls
    through to the generic registry (scout.core.platform.destinations),
    which is how new connectors (elastic, s3, bigquery, ...) plug in without
    touching this router.
    """
    if name == "webhook":
        return WebhookDestination(config=WebhookDestinationConfig(**config))
    if name == "algolia":
        return AlgoliaDestination(config=AlgoliaDestinationConfig(**config))
    return get_destination(name, config)


async def _resolve_records(req: DestinationSendRequest, tenant_id: str) -> list[dict[str, Any]]:
    """Return inline records, or records loaded from an owned run_id."""
    if req.records:
        return req.records
    return await _load_run_records(req.run_id, tenant_id)


async def _load_run_records(run_id: str, tenant_id: str) -> list[dict[str, Any]]:
    """Load records for a hosted run the caller's tenant owns.

    Imported lazily to avoid a hard import-time dependency from this router
    onto the run-store module for callers that only ever pass inline records.
    """
    from scout.api.run_store import artifact_path, get_run

    run = await get_run(run_id)
    if run is None or run.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    path = artifact_path(run, "records_json")
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"No records artifact for run: {run_id}")
    import json

    data = json.loads(path.read_text())
    return data if isinstance(data, list) else []


def _debit_credits(
    account_service: HostedAccountService,
    tenant_id: str,
    key_id: str,
    cost: int,
) -> Any:
    """Atomically debit standard credits and record a usage ledger entry."""
    balance = account_service.store.try_debit_action(tenant_id, _CREDIT_TYPE, cost)
    if balance is None:
        return None
    account_service.store.record_usage(
        HostedUsageLedgerEntry(
            ledger_id=f"usage_{uuid4().hex}",
            tenant_id=tenant_id,
            key_id=key_id,
            action="destination_send",
            credit_type=_CREDIT_TYPE,
            credits=cost,
            standard_balance_after=balance.standard_credits_remaining,
            browser_balance_after=balance.browser_credits_remaining,
        )
    )
    return balance


def _bearer_token(authorization: str) -> str:
    """Extract a Bearer token or reject the hosted request."""
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization[len(prefix) :].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    return token
