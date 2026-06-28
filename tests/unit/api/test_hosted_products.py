"""Tests for hosted bearer-auth products endpoint."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from scout.api.deps import get_crawler, get_hosted_account_service, get_hosted_rate_limiter
from scout.api.main import app
from scout.core.platform.account_service import (
    HostedAccountService,
    InMemoryHostedAccountStore,
)
from scout.core.platform.hosted import HostedPlan, plan_limits
from scout.core.platform.hosted_rate_limit import HostedRateLimitConfig, HostedRateLimiter
from scout.core.types import (
    AlgoliaProductRecord,
    ProductCrawlResponse,
    ProductSource,
)


def _account_service_with_key() -> tuple[HostedAccountService, str, str]:
    service = HostedAccountService(InMemoryHostedAccountStore())
    provisioned = service.provision_account(
        email="builder@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )
    return service, provisioned.raw_api_key, provisioned.tenant.tenant_id


def _product_record(idx: int = 1) -> AlgoliaProductRecord:
    return AlgoliaProductRecord(
        objectID=f"prod_{idx}",
        name=f"Product {idx}",
        url=f"https://shop.example.com/products/{idx}",
        source=ProductSource(
            url=f"https://shop.example.com/products/{idx}",
            extractor="jsonld",
        ),
    )


def _products_response(total_records: int = 2) -> ProductCrawlResponse:
    records = [_product_record(idx) for idx in range(1, total_records + 1)]
    return ProductCrawlResponse(
        success=True,
        query="skin care",
        site="shop.example.com",
        start_url="https://shop.example.com/products",
        records=records,
        total_records=total_records,
        duration_ms=30,
    )


def test_hosted_products_requires_bearer_token() -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    mock_crawler = MagicMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/products",
            json={"start_url": "https://shop.example.com/products"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing Bearer token"


def test_hosted_products_debits_one_standard_credit_per_returned_record() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    mock_crawler = MagicMock()
    mock_crawler.products = AsyncMock(return_value=_products_response(total_records=2))
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/products",
            json={
                "query": "skin care",
                "start_url": "https://shop.example.com/products",
                "max_products": 5,
            },
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["hosted"]["tenant_id"] == tenant_id
    assert data["hosted"]["credits_charged"] == 2
    assert data["hosted"]["credit_type"] == "standard"
    assert data["products"]["total_records"] == 2
    assert raw_key not in resp.text
    assert balance.standard_credits_remaining == limits.standard_credits - 2
    mock_crawler.products.assert_awaited_once()


def test_hosted_products_rejects_max_products_above_plan_limit_without_crawling() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    mock_crawler = MagicMock()
    mock_crawler.products = AsyncMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/products",
            json={
                "start_url": "https://shop.example.com/products",
                "max_products": 101,
            },
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Plan allows at most 100 products per request."
    assert balance.standard_credits_remaining == limits.standard_credits
    assert mock_crawler.products.await_count == 0


def test_hosted_products_rejects_insufficient_preflight_credits_without_crawling() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    account_service.set_balance(tenant_id, standard_credits=1, browser_credits=100)
    mock_crawler = MagicMock()
    mock_crawler.products = AsyncMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/products",
            json={
                "start_url": "https://shop.example.com/products",
                "max_products": 2,
            },
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Insufficient standard credits: need 2, have 1."
    assert balance.standard_credits_remaining == 1
    assert mock_crawler.products.await_count == 0


def test_hosted_products_rate_limit_rejects_without_second_debit_or_crawl() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    limiter = HostedRateLimiter(HostedRateLimitConfig(max_requests=1, window_seconds=60))
    mock_crawler = MagicMock()
    mock_crawler.products = AsyncMock(return_value=_products_response(total_records=1))
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_rate_limiter] = lambda: limiter
    try:
        client = TestClient(app)
        first = client.post(
            "/v1/hosted/products",
            json={
                "start_url": "https://shop.example.com/products",
                "max_products": 1,
            },
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        second = client.post(
            "/v1/hosted/products",
            json={
                "start_url": "https://shop.example.com/products",
                "max_products": 1,
            },
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)
    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["detail"] == "Hosted API rate limit exceeded."
    assert second.headers["retry-after"] == "60"
    assert raw_key not in second.text
    assert mock_crawler.products.await_count == 1
    assert balance.standard_credits_remaining == limits.standard_credits - 1
