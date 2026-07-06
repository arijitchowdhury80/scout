"""Unit + contract tests for the generic Destinations connector system.

Covers:
- DestinationResult contract (Pydantic boundary, no raw dicts).
- WebhookDestination — universal POST connector, timeout + error capture.
- AlgoliaDestination — thin wrapper reusing the existing save_objects integration.
- Registry — name -> connector lookup, extensible for future connectors.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest
from pydantic import ValidationError

from scout.core.platform.destinations import (
    AlgoliaDestination,
    AlgoliaDestinationConfig,
    Destination,
    DestinationResult,
    WebhookDestination,
    WebhookDestinationConfig,
    get_destination,
    list_destinations,
    register_destination,
)

_SAMPLE_RECORDS: list[dict[str, Any]] = [
    {"objectID": "1", "name": "Blue Shirt", "url": "https://example.com/1"},
    {"objectID": "2", "name": "Red Pants", "url": "https://example.com/2"},
]


# ---------------------------------------------------------------------------
# DestinationResult contract
# ---------------------------------------------------------------------------


class TestDestinationResultContract:
    def test_requires_success_field(self) -> None:
        with pytest.raises(ValidationError):
            DestinationResult()  # type: ignore[call-arg]

    def test_defaults(self) -> None:
        result = DestinationResult(success=True, destination="webhook")
        assert result.records_sent == 0
        assert result.errors == []
        assert result.details == {}

    def test_rejects_extra_top_level_junk_via_typed_details(self) -> None:
        # details is a typed dict[str, Any] escape hatch, but the top-level
        # contract fields themselves must stay typed — no raw dict allowed
        # to cross as the return value itself.
        result = DestinationResult(
            success=False,
            destination="webhook",
            errors=["timeout"],
        )
        assert result.success is False
        assert result.errors == ["timeout"]


# ---------------------------------------------------------------------------
# WebhookDestination
# ---------------------------------------------------------------------------


class TestWebhookDestination:
    async def test_posts_records_as_json_to_customer_url(self) -> None:
        captured: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["body"] = request.content
            return httpx.Response(200, json={"ok": True})

        transport = httpx.MockTransport(handler)
        dest = WebhookDestination(
            config=WebhookDestinationConfig(url="https://customer.example.com/hook"),
            transport=transport,
        )
        result = await dest.send(_SAMPLE_RECORDS)

        assert result.success is True
        assert result.destination == "webhook"
        assert result.records_sent == 2
        assert captured["url"] == "https://customer.example.com/hook"
        assert b"Blue Shirt" in captured["body"]

    async def test_non_2xx_response_is_captured_as_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="internal error")

        transport = httpx.MockTransport(handler)
        dest = WebhookDestination(
            config=WebhookDestinationConfig(url="https://customer.example.com/hook"),
            transport=transport,
        )
        result = await dest.send(_SAMPLE_RECORDS)

        assert result.success is False
        assert result.records_sent == 0
        assert any("500" in err for err in result.errors)

    async def test_timeout_is_captured_not_raised(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("connect timeout")

        transport = httpx.MockTransport(handler)
        dest = WebhookDestination(
            config=WebhookDestinationConfig(
                url="https://customer.example.com/hook", timeout_seconds=1.0
            ),
            transport=transport,
        )
        result = await dest.send(_SAMPLE_RECORDS)

        assert result.success is False
        assert result.records_sent == 0
        assert any("timeout" in err.lower() for err in result.errors)

    async def test_connection_error_is_captured_not_raised(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        transport = httpx.MockTransport(handler)
        dest = WebhookDestination(
            config=WebhookDestinationConfig(url="https://customer.example.com/hook"),
            transport=transport,
        )
        result = await dest.send(_SAMPLE_RECORDS)

        assert result.success is False
        assert any("connection refused" in err.lower() for err in result.errors)

    async def test_empty_records_is_a_no_op_success(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"ok": True})

        transport = httpx.MockTransport(handler)
        dest = WebhookDestination(
            config=WebhookDestinationConfig(url="https://customer.example.com/hook"),
            transport=transport,
        )
        result = await dest.send([])
        assert result.success is True
        assert result.records_sent == 0

    def test_config_requires_url(self) -> None:
        with pytest.raises(ValidationError):
            WebhookDestinationConfig()  # type: ignore[call-arg]

    def test_config_rejects_non_http_scheme(self) -> None:
        with pytest.raises(ValidationError):
            WebhookDestinationConfig(url="ftp://example.com/hook")

    def test_is_a_destination_protocol_implementation(self) -> None:
        dest = WebhookDestination(
            config=WebhookDestinationConfig(url="https://customer.example.com/hook")
        )
        assert isinstance(dest, Destination)


# ---------------------------------------------------------------------------
# AlgoliaDestination — wraps the EXISTING save_objects integration
# ---------------------------------------------------------------------------


class TestAlgoliaDestination:
    async def test_send_calls_save_objects_with_correct_args(self) -> None:
        mock_response = MagicMock()
        mock_response.object_ids = ["1", "2"]
        with patch("scout.core.platform.destinations.SearchClientSync") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.save_objects.return_value = [mock_response]

            dest = AlgoliaDestination(
                config=AlgoliaDestinationConfig(
                    app_id="TESTAPP", api_key="test-key", index_name="products"
                )
            )
            result = await dest.send(_SAMPLE_RECORDS)

        mock_cls.assert_called_once_with(app_id="TESTAPP", api_key="test-key")
        mock_client.save_objects.assert_called_once()
        call_kwargs = mock_client.save_objects.call_args.kwargs
        assert call_kwargs["index_name"] == "products"
        assert call_kwargs["objects"] == _SAMPLE_RECORDS
        assert result.success is True
        assert result.destination == "algolia"
        assert result.records_sent == 2

    async def test_send_captures_sdk_errors(self) -> None:
        with patch("scout.core.platform.destinations.SearchClientSync") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.save_objects.side_effect = Exception("rate limit exceeded")

            dest = AlgoliaDestination(
                config=AlgoliaDestinationConfig(
                    app_id="TESTAPP", api_key="test-key", index_name="products"
                )
            )
            result = await dest.send(_SAMPLE_RECORDS)

        assert result.success is False
        assert result.records_sent == 0
        assert any("rate limit exceeded" in err for err in result.errors)

    async def test_send_rejects_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            AlgoliaDestinationConfig(app_id="", api_key="key", index_name="idx")

    def test_is_a_destination_protocol_implementation(self) -> None:
        dest = AlgoliaDestination(
            config=AlgoliaDestinationConfig(app_id="A", api_key="K", index_name="I")
        )
        assert isinstance(dest, Destination)


# ---------------------------------------------------------------------------
# Registry — name -> connector, extensible for elastic/s3/bigquery later
# ---------------------------------------------------------------------------


class TestDestinationRegistry:
    def test_lists_builtin_destinations(self) -> None:
        names = list_destinations()
        assert "webhook" in names
        assert "algolia" in names

    def test_get_destination_builds_webhook_from_config(self) -> None:
        dest = get_destination("webhook", {"url": "https://example.com/hook"})
        assert isinstance(dest, WebhookDestination)

    def test_get_destination_builds_algolia_from_config(self) -> None:
        dest = get_destination(
            "algolia",
            {"app_id": "A", "api_key": "K", "index_name": "I"},
        )
        assert isinstance(dest, AlgoliaDestination)

    def test_get_destination_unknown_name_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            get_destination("bigquery", {})

    def test_register_destination_allows_future_connectors(self) -> None:
        class _FakeConfig(dict):
            pass

        def _factory(config: dict[str, Any]) -> Destination:
            return WebhookDestination(config=WebhookDestinationConfig(url=config["url"]))

        register_destination("fake_future_connector", _factory)
        try:
            assert "fake_future_connector" in list_destinations()
            dest = get_destination("fake_future_connector", {"url": "https://example.com/hook"})
            assert isinstance(dest, WebhookDestination)
        finally:
            # cleanup so this test doesn't pollute the shared module-level registry
            from scout.core.platform.destinations import _REGISTRY

            _REGISTRY.pop("fake_future_connector", None)
