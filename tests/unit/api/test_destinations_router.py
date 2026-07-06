"""Contract tests for POST /v1/hosted/destinations/send.

This router is NOT wired into scout/api/main.py yet (a later step does that),
so these tests mount scout.api.routers.destinations.router on a standalone
FastAPI app — the same pattern main.py will use once it's wired in.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from scout.api.deps import get_hosted_account_service
from scout.api.routers.destinations import router
from scout.core.platform.account_service import (
    HostedAccountService,
    InMemoryHostedAccountStore,
)
from scout.core.platform.destinations import DestinationResult
from scout.core.platform.hosted import HostedPlan, plan_limits

_SAMPLE_RECORDS: list[dict[str, Any]] = [
    {"objectID": "1", "name": "Blue Shirt", "url": "https://example.com/1"},
    {"objectID": "2", "name": "Red Pants", "url": "https://example.com/2"},
]


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


def _account_service_with_key() -> tuple[HostedAccountService, str, str]:
    service = HostedAccountService(InMemoryHostedAccountStore())
    provisioned = service.provision_account(
        email="builder@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )
    return service, provisioned.raw_api_key, provisioned.tenant.tenant_id


class TestDestinationsSendAuth:
    def test_requires_bearer_token(self) -> None:
        app = _make_app()
        account_service, _raw_key, _tenant_id = _account_service_with_key()
        app.dependency_overrides[get_hosted_account_service] = lambda: account_service
        client = TestClient(app)

        resp = client.post(
            "/v1/hosted/destinations/send",
            json={
                "destination": "webhook",
                "config": {"url": "https://customer.example.com/hook"},
                "records": _SAMPLE_RECORDS,
            },
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Missing Bearer token"

    def test_rejects_invalid_bearer_token(self) -> None:
        app = _make_app()
        account_service, _raw_key, _tenant_id = _account_service_with_key()
        app.dependency_overrides[get_hosted_account_service] = lambda: account_service
        client = TestClient(app)

        resp = client.post(
            "/v1/hosted/destinations/send",
            json={
                "destination": "webhook",
                "config": {"url": "https://customer.example.com/hook"},
                "records": _SAMPLE_RECORDS,
            },
            headers={"Authorization": "Bearer not-a-real-key"},
        )
        assert resp.status_code == 403


class TestDestinationsSendValidation:
    def test_unknown_destination_returns_400(self) -> None:
        app = _make_app()
        account_service, raw_key, _tenant_id = _account_service_with_key()
        app.dependency_overrides[get_hosted_account_service] = lambda: account_service
        client = TestClient(app)

        resp = client.post(
            "/v1/hosted/destinations/send",
            json={
                "destination": "bigquery",
                "config": {},
                "records": _SAMPLE_RECORDS,
            },
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        assert resp.status_code == 400
        assert "bigquery" in resp.json()["detail"]

    def test_requires_records_or_run_id(self) -> None:
        app = _make_app()
        account_service, raw_key, _tenant_id = _account_service_with_key()
        app.dependency_overrides[get_hosted_account_service] = lambda: account_service
        client = TestClient(app)

        resp = client.post(
            "/v1/hosted/destinations/send",
            json={
                "destination": "webhook",
                "config": {"url": "https://customer.example.com/hook"},
            },
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        assert resp.status_code == 422

    def test_invalid_config_for_destination_returns_422(self) -> None:
        app = _make_app()
        account_service, raw_key, _tenant_id = _account_service_with_key()
        app.dependency_overrides[get_hosted_account_service] = lambda: account_service
        client = TestClient(app)

        resp = client.post(
            "/v1/hosted/destinations/send",
            json={
                "destination": "webhook",
                "config": {},  # missing required url
                "records": _SAMPLE_RECORDS,
            },
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        assert resp.status_code == 422


class TestDestinationsSendWebhook:
    def test_sends_records_and_debits_one_credit_per_record(self) -> None:
        app = _make_app()
        account_service, raw_key, tenant_id = _account_service_with_key()
        app.dependency_overrides[get_hosted_account_service] = lambda: account_service

        fake_result = DestinationResult(success=True, destination="webhook", records_sent=2)
        with patch("scout.api.routers.destinations.WebhookDestination") as mock_dest_cls:
            mock_dest_cls.return_value.send = AsyncMock(return_value=fake_result)
            client = TestClient(app)
            resp = client.post(
                "/v1/hosted/destinations/send",
                json={
                    "destination": "webhook",
                    "config": {"url": "https://customer.example.com/hook"},
                    "records": _SAMPLE_RECORDS,
                },
                headers={"Authorization": f"Bearer {raw_key}"},
            )

        limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)
        balance = account_service.get_balance(tenant_id)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["result"]["destination"] == "webhook"
        assert data["result"]["records_sent"] == 2
        assert data["hosted"]["credits_charged"] == 2
        assert data["hosted"]["credit_type"] == "standard"
        assert balance.standard_credits_remaining == limits.standard_credits - 2

    def test_insufficient_credits_returns_402_without_calling_destination(self) -> None:
        app = _make_app()
        account_service = HostedAccountService(InMemoryHostedAccountStore())
        provisioned = account_service.provision_account(
            email="poor@example.com",
            plan=HostedPlan.HOSTED_BETA_PASS,
            scopes=["runs:create"],
            standard_credits=1,
        )
        app.dependency_overrides[get_hosted_account_service] = lambda: account_service
        client = TestClient(app)

        with patch("scout.api.routers.destinations.WebhookDestination") as mock_dest_cls:
            resp = client.post(
                "/v1/hosted/destinations/send",
                json={
                    "destination": "webhook",
                    "config": {"url": "https://customer.example.com/hook"},
                    "records": _SAMPLE_RECORDS,  # 2 records, only 1 credit available
                },
                headers={"Authorization": f"Bearer {provisioned.raw_api_key}"},
            )

        assert resp.status_code == 402
        mock_dest_cls.assert_not_called()


class TestDestinationsSendAlgolia:
    def test_sends_records_via_existing_save_objects_integration(self) -> None:
        app = _make_app()
        account_service, raw_key, tenant_id = _account_service_with_key()
        app.dependency_overrides[get_hosted_account_service] = lambda: account_service

        mock_response = MagicMock()
        mock_response.object_ids = ["1", "2"]
        with patch("scout.core.platform.destinations.SearchClientSync") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.save_objects.return_value = [mock_response]
            client = TestClient(app)
            resp = client.post(
                "/v1/hosted/destinations/send",
                json={
                    "destination": "algolia",
                    "config": {
                        "app_id": "TESTAPP",
                        "api_key": "test-key",
                        "index_name": "products",
                    },
                    "records": _SAMPLE_RECORDS,
                },
                headers={"Authorization": f"Bearer {raw_key}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["result"]["destination"] == "algolia"
        assert data["result"]["records_sent"] == 2
        assert data["hosted"]["credits_charged"] == 2

    def test_algolia_credentials_never_echoed_in_response(self) -> None:
        app = _make_app()
        account_service, raw_key, _tenant_id = _account_service_with_key()
        app.dependency_overrides[get_hosted_account_service] = lambda: account_service

        mock_response = MagicMock()
        mock_response.object_ids = ["1"]
        with patch("scout.core.platform.destinations.SearchClientSync") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.save_objects.return_value = [mock_response]
            client = TestClient(app)
            resp = client.post(
                "/v1/hosted/destinations/send",
                json={
                    "destination": "algolia",
                    "config": {
                        "app_id": "TESTAPP",
                        "api_key": "super-secret-admin-key",
                        "index_name": "products",
                    },
                    "records": [_SAMPLE_RECORDS[0]],
                },
                headers={"Authorization": f"Bearer {raw_key}"},
            )

        assert "super-secret-admin-key" not in resp.text
