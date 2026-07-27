"""LLM extraction fallback gating for the products mode.

Heuristic-first, cost-bounded: the LLM fallback must fire ONLY when (a)
heuristic extraction (JSON-LD/listing cards/browser fallback) found zero
product records for the whole run, AND (b) an LLM key was actually passed
in (the caller's job — see ScoutCrawler.fallback_llm_api_key). These tests
never call a real LLM; scout.core.modes.products.llm_extract_products is
always mocked.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from scout.core.llm_extract import LLMProductItem
from scout.core.modes.products import products
from scout.core.products.discovery import ProductUrlGroups
from scout.core.products.jsonld import ProductJsonLd
from scout.core.types import MapResponse, ProductCrawlRequest, ScrapeResponse, ScoutMetadata


def _meta(url: str, title: str = "") -> ScoutMetadata:
    return ScoutMetadata(url=url, crawled_at="2026-07-27T00:00:00Z", title=title)


def _no_urls_map_response(start_url: str) -> MapResponse:
    return MapResponse(success=True, start_url=start_url, urls=[], total=0, duration_ms=5)


@pytest.mark.asyncio
async def test_llm_fallback_not_called_when_heuristics_found_records() -> None:
    """Heuristics find a real product via JSON-LD -> LLM must never run."""
    group = ProductUrlGroups(
        category_url="https://shop.example.com/cat",
        category_name="Cat",
        product_urls=["https://shop.example.com/cat/p1"],
        listing_cards=[],
    )

    async def _fake_scrape(req):
        return ScrapeResponse(
            success=True,
            url=req.url,
            markdown="# Oxford Shirt",
            raw_html="<html></html>",
            metadata=_meta(req.url, "Oxford Shirt"),
            duration_ms=10,
        )

    with (
        patch(
            "scout.core.modes.products.map_urls",
            new_callable=AsyncMock,
            return_value=_no_urls_map_response("https://shop.example.com"),
        ),
        patch(
            "scout.core.modes.products._discover_from_categories",
            new_callable=AsyncMock,
            return_value=[group],
        ),
        patch("scout.core.modes.products.scrape", side_effect=_fake_scrape),
        patch(
            "scout.core.modes.products.extract_product_jsonld",
            return_value=ProductJsonLd(name="Oxford Shirt", price=49.0, currency="USD"),
        ),
        patch("scout.core.modes.products.llm_extract_products", new_callable=AsyncMock) as mock_llm,
    ):
        req = ProductCrawlRequest(start_url="https://shop.example.com/cat", max_products=10)
        resp = await products(req, llm_api_key="fake-anthropic-key")

    mock_llm.assert_not_called()
    assert resp.total_records == 1
    assert resp.records[0].name == "Oxford Shirt"


@pytest.mark.asyncio
async def test_llm_fallback_called_when_heuristics_empty_and_llm_enabled() -> None:
    """Heuristics find nothing at all -> LLM fallback fires and its records are used."""
    with (
        patch(
            "scout.core.modes.products.map_urls",
            new_callable=AsyncMock,
            return_value=_no_urls_map_response("https://shop.example.com"),
        ),
        patch(
            "scout.core.modes.products._discover_from_categories",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "scout.core.modes.products.scrape",
            new_callable=AsyncMock,
            return_value=ScrapeResponse(
                success=True,
                url="https://shop.example.com",
                markdown="# Weird catalog markup the heuristics can't parse",
                metadata=_meta("https://shop.example.com"),
                duration_ms=10,
            ),
        ),
        patch(
            "scout.core.modes.products.llm_extract_products",
            new_callable=AsyncMock,
            return_value=[
                LLMProductItem(name="Mystery Widget", price=12.5, currency="USD", url=""),
            ],
        ) as mock_llm,
    ):
        req = ProductCrawlRequest(start_url="https://shop.example.com", max_products=10)
        resp = await products(req, llm_api_key="fake-anthropic-key")

    mock_llm.assert_called_once()
    assert resp.total_records == 1
    assert resp.records[0].name == "Mystery Widget"
    assert resp.records[0].source.extractor == "llm_fallback"
    assert resp.blocked_pages == []


@pytest.mark.asyncio
async def test_llm_fallback_never_called_when_llm_disabled() -> None:
    """No llm_api_key passed (fallback disabled/unconfigured) -> LLM must never run."""
    with (
        patch(
            "scout.core.modes.products.map_urls",
            new_callable=AsyncMock,
            return_value=_no_urls_map_response("https://shop.example.com"),
        ),
        patch(
            "scout.core.modes.products._discover_from_categories",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch("scout.core.modes.products.scrape", new_callable=AsyncMock) as mock_scrape,
        patch("scout.core.modes.products.llm_extract_products", new_callable=AsyncMock) as mock_llm,
    ):
        req = ProductCrawlRequest(start_url="https://shop.example.com", max_products=10)
        resp = await products(req)  # llm_api_key defaults to ""

    mock_llm.assert_not_called()
    mock_scrape.assert_not_called()
    assert resp.total_records == 0
    assert resp.blocked_pages[0].reason == "no_product_records"
    assert resp.blocked_pages[0].fallback_attempted is False
