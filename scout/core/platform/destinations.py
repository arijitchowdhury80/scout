"""Generic Destinations connector system.

A `Destination` is anything Scout can push records to: a customer webhook,
Algolia, and — later — Elasticsearch, S3, BigQuery, etc. Every connector
implements the same `send(records) -> DestinationResult` interface so the
API layer and the UI never need to know which backend they're talking to.

Frontend-facing framing (see docs/product/design-system.md +
docs/product/plg-playground-ux.md): this is "Exports + Destinations — push
to your search index, warehouse, or webhook." Algolia is one connector among
several, not the headline.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import httpx
import structlog
from algoliasearch.search.client import SearchClientSync
from pydantic import AnyUrl, BaseModel, Field, field_validator

logger = structlog.get_logger(__name__)

_DEFAULT_WEBHOOK_TIMEOUT_SECONDS = 15.0


class DestinationResult(BaseModel):
    """Typed result returned by every destination's `send()` call.

    No raw dicts cross this boundary — callers get a Pydantic model whether
    the push succeeded, partially succeeded, or failed outright.
    """

    success: bool
    destination: str
    records_sent: int = 0
    errors: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class Destination(Protocol):
    """Structural interface every connector implements."""

    async def send(self, records: list[dict[str, Any]]) -> DestinationResult: ...


# ---------------------------------------------------------------------------
# Webhook — universal connector, no vendor lock-in
# ---------------------------------------------------------------------------


class WebhookDestinationConfig(BaseModel):
    """Configuration for a customer-owned webhook destination."""

    url: AnyUrl
    headers: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: float = Field(default=_DEFAULT_WEBHOOK_TIMEOUT_SECONDS, gt=0)

    @field_validator("url")
    @classmethod
    def _require_http_scheme(cls, value: AnyUrl) -> AnyUrl:
        if value.scheme not in {"http", "https"}:
            raise ValueError(f"Webhook URL must be http(s), got scheme: {value.scheme}")
        return value


class WebhookDestination:
    """POST records as JSON to a customer-owned URL.

    This is the universal connector — no vendor lock-in. Any system that can
    receive a JSON POST (Zapier, a customer's own service, a queue ingester)
    works without Scout knowing anything about it.
    """

    name = "webhook"

    def __init__(
        self,
        config: WebhookDestinationConfig,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.config = config
        self._transport = transport

    async def send(self, records: list[dict[str, Any]]) -> DestinationResult:
        if not records:
            return DestinationResult(success=True, destination=self.name, records_sent=0)

        payload = {"records": records, "record_count": len(records)}
        try:
            async with httpx.AsyncClient(
                transport=self._transport,
                timeout=self.config.timeout_seconds,
            ) as client:
                response = await client.post(
                    str(self.config.url),
                    json=payload,
                    headers=self.config.headers,
                )
            if 200 <= response.status_code < 300:
                return DestinationResult(
                    success=True,
                    destination=self.name,
                    records_sent=len(records),
                    details={"status_code": response.status_code},
                )
            logger.warning(
                "webhook_destination_non_2xx",
                status_code=response.status_code,
                url=str(self.config.url),
            )
            return DestinationResult(
                success=False,
                destination=self.name,
                records_sent=0,
                errors=[f"Webhook returned HTTP {response.status_code}: {response.text[:240]}"],
                details={"status_code": response.status_code},
            )
        except httpx.TimeoutException as exc:
            logger.warning("webhook_destination_timeout", url=str(self.config.url), error=str(exc))
            return DestinationResult(
                success=False,
                destination=self.name,
                records_sent=0,
                errors=[f"Webhook request timed out: {exc}"],
            )
        except httpx.HTTPError as exc:
            logger.warning("webhook_destination_error", url=str(self.config.url), error=str(exc))
            return DestinationResult(
                success=False,
                destination=self.name,
                records_sent=0,
                errors=[f"Webhook request failed: {exc}"],
            )


# ---------------------------------------------------------------------------
# Algolia — wraps the EXISTING save_objects integration (Plan Phase 3)
# ---------------------------------------------------------------------------


class AlgoliaDestinationConfig(BaseModel):
    """Configuration for an Algolia destination.

    Mirrors the fields already accepted by `POST /algolia/push`
    (scout/api/routers/algolia.py) — this connector reuses that same
    save_objects call, it does not reimplement it.
    """

    app_id: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    index_name: str = Field(min_length=1)
    batch_size: int = Field(default=1000, gt=0)


class AlgoliaDestination:
    """Push records to an Algolia index via the existing save_objects integration."""

    name = "algolia"

    def __init__(self, config: AlgoliaDestinationConfig) -> None:
        self.config = config

    async def send(self, records: list[dict[str, Any]]) -> DestinationResult:
        if not records:
            return DestinationResult(success=True, destination=self.name, records_sent=0)
        try:
            client = SearchClientSync(app_id=self.config.app_id, api_key=self.config.api_key)
            responses = client.save_objects(
                index_name=self.config.index_name,
                objects=records,
                batch_size=self.config.batch_size,
            )
            object_ids: list[str] = []
            for batch_resp in responses:
                object_ids.extend(batch_resp.object_ids)
            return DestinationResult(
                success=True,
                destination=self.name,
                records_sent=len(object_ids),
                details={"index_name": self.config.index_name, "object_ids": object_ids},
            )
        except Exception as exc:  # noqa: BLE001 - external SDK, capture not raise
            logger.warning(
                "algolia_destination_error",
                index_name=self.config.index_name,
                error=str(exc),
            )
            return DestinationResult(
                success=False,
                destination=self.name,
                records_sent=0,
                errors=[str(exc)],
            )


# ---------------------------------------------------------------------------
# Registry — name -> connector factory, extensible for elastic/s3/bigquery
# ---------------------------------------------------------------------------

DestinationFactory = Any  # Callable[[dict[str, Any]], Destination]


def _build_webhook(config: dict[str, Any]) -> Destination:
    return WebhookDestination(config=WebhookDestinationConfig(**config))


def _build_algolia(config: dict[str, Any]) -> Destination:
    return AlgoliaDestination(config=AlgoliaDestinationConfig(**config))


_REGISTRY: dict[str, DestinationFactory] = {
    "webhook": _build_webhook,
    "algolia": _build_algolia,
}


def list_destinations() -> list[str]:
    """Return the names of all registered destination connectors."""
    return list(_REGISTRY)


def get_destination(name: str, config: dict[str, Any]) -> Destination:
    """Build a destination connector by name from raw config.

    Raises KeyError if `name` is not a registered connector, and
    pydantic.ValidationError if `config` doesn't match that connector's
    config schema.
    """
    factory = _REGISTRY.get(name)
    if factory is None:
        raise KeyError(f"Unknown destination: {name}. Available: {list_destinations()}")
    return factory(config)


def register_destination(name: str, factory: DestinationFactory) -> None:
    """Register a new destination connector (e.g. elastic, s3, bigquery).

    Drop-in extension point: future connectors call this once at import
    time instead of modifying this module.
    """
    _REGISTRY[name] = factory
