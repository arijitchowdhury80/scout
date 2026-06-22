"""Tests for POST /algolia/push — Algolia record ingestion endpoint."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from scout.api.main import app

_HEADERS = {"X-API-Key": "dev-key"}

_SAMPLE_RECORDS: list[dict[str, Any]] = [
    {"objectID": "prod_1", "name": "Blue Shirt", "url": "https://example.com/1"},
    {"objectID": "prod_2", "name": "Red Pants", "url": "https://example.com/2"},
]


@pytest.fixture
def _mock_lifespan():
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def noop(_app):
        yield

    original = app.router.lifespan_context
    app.router.lifespan_context = noop
    yield
    app.router.lifespan_context = original


class TestAlgoliaPush:
    def test_push_success(self, _mock_lifespan) -> None:
        mock_response = MagicMock()
        mock_response.object_ids = ["prod_1", "prod_2"]
        with patch("scout.api.routers.algolia.SearchClientSync") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.save_objects.return_value = [mock_response]
            client = TestClient(app)
            resp = client.post(
                "/algolia/push",
                json={
                    "app_id": "TESTAPP",
                    "api_key": "test-key-123",
                    "index_name": "products",
                    "records": _SAMPLE_RECORDS,
                },
                headers=_HEADERS,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["index_name"] == "products"
        assert data["records_pushed"] == 2
        assert "prod_1" in data["object_ids"]
        assert "prod_2" in data["object_ids"]

    def test_push_calls_save_objects_with_correct_args(self, _mock_lifespan) -> None:
        mock_response = MagicMock()
        mock_response.object_ids = ["prod_1"]
        with patch("scout.api.routers.algolia.SearchClientSync") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.save_objects.return_value = [mock_response]
            client = TestClient(app)
            client.post(
                "/algolia/push",
                json={
                    "app_id": "MY_APP",
                    "api_key": "my-key",
                    "index_name": "test_idx",
                    "records": [_SAMPLE_RECORDS[0]],
                    "batch_size": 500,
                },
                headers=_HEADERS,
            )
            mock_cls.assert_called_once_with(app_id="MY_APP", api_key="my-key")
            mock_client.save_objects.assert_called_once()
            call_kwargs = mock_client.save_objects.call_args
            assert call_kwargs.kwargs["index_name"] == "test_idx"
            assert call_kwargs.kwargs["batch_size"] == 500

    def test_push_missing_credentials_returns_422(self, _mock_lifespan) -> None:
        client = TestClient(app)
        resp = client.post(
            "/algolia/push",
            json={
                "app_id": "",
                "api_key": "",
                "index_name": "products",
                "records": _SAMPLE_RECORDS,
            },
            headers=_HEADERS,
        )
        assert resp.status_code == 422

    def test_push_empty_records_returns_422(self, _mock_lifespan) -> None:
        client = TestClient(app)
        resp = client.post(
            "/algolia/push",
            json={
                "app_id": "APP",
                "api_key": "KEY",
                "index_name": "products",
                "records": [],
            },
            headers=_HEADERS,
        )
        assert resp.status_code == 422

    def test_push_sdk_error_returns_error_response(self, _mock_lifespan) -> None:
        with patch("scout.api.routers.algolia.SearchClientSync") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.save_objects.side_effect = Exception("API rate limit exceeded")
            client = TestClient(app)
            resp = client.post(
                "/algolia/push",
                json={
                    "app_id": "APP",
                    "api_key": "KEY",
                    "index_name": "products",
                    "records": _SAMPLE_RECORDS,
                },
                headers=_HEADERS,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "API rate limit exceeded" in data["errors"][0]

    def test_push_updates_ingest_supported_flag(self, _mock_lifespan) -> None:
        client = TestClient(app)
        resp = client.post(
            "/algolia/preview",
            json={
                "app_id": "APP",
                "api_key": "KEY",
                "index_name": "idx",
                "records": _SAMPLE_RECORDS,
            },
            headers=_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["ingest_supported"] is True
