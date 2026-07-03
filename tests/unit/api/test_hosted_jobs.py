"""Tests for hosted async job queue behavior."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from scout.api.deps import (
    get_crawler,
    get_hosted_account_service,
    get_hosted_admission_controller,
    get_hosted_job_queue,
)
from scout.api.hosted_jobs import HostedJobQueue
from scout.api.main import app
from scout.core.platform.account_service import (
    HostedAccountService,
    InMemoryHostedAccountStore,
)
from scout.core.platform.admission import AdmissionController
from scout.core.platform.hosted import HostedPlan, plan_limits
from scout.core.types import ScoutMetadata, ScrapeResponse


def _account_service_with_key() -> tuple[HostedAccountService, str, str]:
    service = HostedAccountService(InMemoryHostedAccountStore())
    provisioned = service.provision_account(
        email="builder@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )
    return service, provisioned.raw_api_key, provisioned.tenant.tenant_id


def test_hosted_scrape_capacity_full_accepts_queued_job_without_debit_or_crawl() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    admission = AdmissionController(max_active=0, retry_after_seconds=3)
    queue = HostedJobQueue(max_queued=2, worker_count=1)
    mock_crawler = MagicMock()
    mock_crawler.scrape = AsyncMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_admission_controller] = lambda: admission
    app.dependency_overrides[get_hosted_job_queue] = lambda: queue
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/scrape",
            json={"url": "https://example.com"},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        data = resp.json()
        job_resp = client.get(
            data["job_url"],
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)
    assert resp.status_code == 202
    assert data["success"] is True
    assert data["status"] == "queued"
    assert data["kind"] == "scrape"
    assert data["job_url"].startswith("/v1/hosted/jobs/job_")
    assert resp.headers["retry-after"] == "3"
    assert job_resp.status_code == 200
    assert job_resp.json()["status"] == "queued"
    assert raw_key not in resp.text
    assert raw_key not in job_resp.text
    assert mock_crawler.scrape.await_count == 0
    assert balance.standard_credits_remaining == limits.standard_credits


def test_hosted_expensive_endpoints_queue_when_worker_capacity_is_full() -> None:
    account_service, raw_key, _tenant_id = _account_service_with_key()
    admission = AdmissionController(max_active=0, retry_after_seconds=3)
    queue = HostedJobQueue(max_queued=4, worker_count=1)
    mock_crawler = MagicMock()
    mock_crawler.crawl = AsyncMock()
    mock_crawler.products = AsyncMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_admission_controller] = lambda: admission
    app.dependency_overrides[get_hosted_job_queue] = lambda: queue
    try:
        client = TestClient(app)
        responses = [
            client.post(
                "/v1/hosted/crawl",
                json={"url": "https://example.com", "max_pages": 2},
                headers={"Authorization": f"Bearer {raw_key}"},
            ),
            client.post(
                "/v1/hosted/products",
                json={"start_url": "https://shop.example.com/products", "max_products": 2},
                headers={"Authorization": f"Bearer {raw_key}"},
            ),
            client.post(
                "/v1/hosted/run/company",
                json={"query": "Microsoft", "mode": "saved", "max_records": 2},
                headers={"Authorization": f"Bearer {raw_key}"},
            ),
        ]
    finally:
        app.dependency_overrides.clear()

    assert [response.status_code for response in responses] == [202, 202, 202]
    assert [response.json()["status"] for response in responses] == ["queued", "queued", "queued"]
    assert [response.json()["kind"] for response in responses] == [
        "crawl",
        "products",
        "run:company",
    ]
    assert mock_crawler.crawl.await_count == 0
    assert mock_crawler.products.await_count == 0


def test_hosted_scrape_async_first_queues_without_waiting_for_capacity(
    monkeypatch,
) -> None:
    monkeypatch.setattr("scout.api.routers.hosted.settings.hosted_async_first", True)
    account_service, raw_key, tenant_id = _account_service_with_key()
    admission = AdmissionController(max_active=100, retry_after_seconds=3)
    queue = HostedJobQueue(max_queued=2, worker_count=1)
    mock_crawler = MagicMock()
    mock_crawler.scrape = AsyncMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_admission_controller] = lambda: admission
    app.dependency_overrides[get_hosted_job_queue] = lambda: queue
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/scrape",
            json={"url": "https://example.com"},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    assert resp.status_code == 202
    data = resp.json()
    assert data["kind"] == "scrape"
    assert data["status"] == "queued"
    assert data["hosted"]["credits_charged"] == 0
    assert mock_crawler.scrape.await_count == 0
    assert (
        balance.standard_credits_remaining
        == plan_limits(HostedPlan.HOSTED_BETA_PASS).standard_credits
    )


def test_hosted_async_first_queues_all_expensive_endpoint_types(monkeypatch) -> None:
    monkeypatch.setattr("scout.api.routers.hosted.settings.hosted_async_first", True)
    account_service, raw_key, _tenant_id = _account_service_with_key()
    admission = AdmissionController(max_active=100, retry_after_seconds=3)
    queue = HostedJobQueue(max_queued=4, worker_count=1)
    mock_crawler = MagicMock()
    mock_crawler.crawl = AsyncMock()
    mock_crawler.products = AsyncMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_admission_controller] = lambda: admission
    app.dependency_overrides[get_hosted_job_queue] = lambda: queue
    try:
        client = TestClient(app)
        responses = [
            client.post(
                "/v1/hosted/crawl",
                json={"url": "https://example.com", "max_pages": 2},
                headers={"Authorization": f"Bearer {raw_key}"},
            ),
            client.post(
                "/v1/hosted/products",
                json={"start_url": "https://shop.example.com/products", "max_products": 2},
                headers={"Authorization": f"Bearer {raw_key}"},
            ),
            client.post(
                "/v1/hosted/run/company",
                json={"query": "Microsoft", "mode": "saved", "max_records": 2},
                headers={"Authorization": f"Bearer {raw_key}"},
            ),
        ]
    finally:
        app.dependency_overrides.clear()

    assert [response.status_code for response in responses] == [202, 202, 202]
    assert [response.json()["kind"] for response in responses] == [
        "crawl",
        "products",
        "run:company",
    ]
    assert mock_crawler.crawl.await_count == 0
    assert mock_crawler.products.await_count == 0


def test_hosted_async_queue_without_workers_rejects_instead_of_fake_accepting(
    monkeypatch,
) -> None:
    monkeypatch.setattr("scout.api.routers.hosted.settings.hosted_async_first", True)
    account_service, raw_key, tenant_id = _account_service_with_key()
    queue = HostedJobQueue(max_queued=4, worker_count=0, retry_after_seconds=7)
    mock_crawler = MagicMock()
    mock_crawler.scrape = AsyncMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_job_queue] = lambda: queue
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/scrape",
            json={"url": "https://example.com"},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    assert resp.status_code == 429
    assert resp.headers["retry-after"] == "7"
    assert resp.json()["detail"] == "Hosted async queue has no workers; retry shortly."
    assert mock_crawler.scrape.await_count == 0
    assert (
        balance.standard_credits_remaining
        == plan_limits(HostedPlan.HOSTED_BETA_PASS).standard_credits
    )


def test_hosted_job_polling_returns_result_after_worker_completes() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    admission = AdmissionController(max_active=0, retry_after_seconds=3)
    queue = HostedJobQueue(max_queued=2, worker_count=1)
    mock_crawler = MagicMock()
    mock_crawler.scrape = AsyncMock(
        return_value=ScrapeResponse(
            success=True,
            url="https://example.com",
            markdown="# Hello",
            metadata=ScoutMetadata(url="https://example.com", crawled_at="2026-06-28T12:00:00Z"),
            provider="test",
            duration_ms=10,
        )
    )
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_admission_controller] = lambda: admission
    app.dependency_overrides[get_hosted_job_queue] = lambda: queue
    try:
        client = TestClient(app)
        accepted = client.post(
            "/v1/hosted/scrape",
            json={"url": "https://example.com"},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        queue.run_next_sync_for_tests()
        job_resp = client.get(
            accepted.json()["job_url"],
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    assert accepted.status_code == 202
    assert job_resp.status_code == 200
    data = job_resp.json()
    assert data["status"] == "complete"
    assert data["result"]["scrape"]["markdown"] == "# Hello"
    assert data["result"]["hosted"]["credits_charged"] == 1
    assert mock_crawler.scrape.await_count == 1
    assert (
        balance.standard_credits_remaining
        == plan_limits(HostedPlan.HOSTED_BETA_PASS).standard_credits - 1
    )


def test_hosted_job_polling_hides_other_tenant_jobs() -> None:
    account_service, raw_key, _tenant_id = _account_service_with_key()
    other_service = account_service.provision_account(
        email="other@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )
    queue = HostedJobQueue(max_queued=2, worker_count=0)
    job = queue.enqueue_sync_for_tests(
        kind="scrape",
        tenant_id=other_service.tenant.tenant_id,
        key_id=other_service.api_key.key_id,
        retry_after_seconds=3,
        work=lambda: {"success": True},
    )
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_job_queue] = lambda: queue
    try:
        client = TestClient(app)
        resp = client.get(
            f"/v1/hosted/jobs/{job.job_id}",
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"] == f"Job not found: {job.job_id}"
