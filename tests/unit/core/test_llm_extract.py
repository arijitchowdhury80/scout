"""Tests for the LLM extraction fallback helper — mocks the LLM call, never hits the network."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from scout.core.llm_extract import (
    LLMExecutiveItem,
    LLMProductItem,
    llm_extract_executives,
    llm_extract_products,
    llm_extract_records,
)


def _fake_extract_products(url, ix, html):
    return [
        {
            "name": "Widget Pro",
            "price": 19.99,
            "currency": "USD",
            "url": "https://x.com/widget",
            "error": False,
        },
        {"name": "Gadget Max", "error": False},
    ]


def _fake_extract_executives(url, ix, html):
    return [
        {"name": "Jane Doe", "title": "CEO", "error": False},
        {"name": "John Roe", "error": False},
    ]


@pytest.mark.asyncio
async def test_llm_extract_products_returns_validated_items() -> None:
    with patch(
        "scout.core.llm_extract.LLMExtractionStrategy.extract",
        side_effect=_fake_extract_products,
    ):
        items = await llm_extract_products(
            "some markdown content", "fake-key", page_url="https://x.com"
        )

    assert len(items) == 2
    assert all(isinstance(item, LLMProductItem) for item in items)
    assert items[0].name == "Widget Pro"
    assert items[0].price == 19.99
    assert items[0].currency == "USD"
    assert items[1].name == "Gadget Max"
    assert items[1].price is None


@pytest.mark.asyncio
async def test_llm_extract_executives_returns_validated_items() -> None:
    with patch(
        "scout.core.llm_extract.LLMExtractionStrategy.extract",
        side_effect=_fake_extract_executives,
    ):
        items = await llm_extract_executives(
            "some markdown content", "fake-key", page_url="https://x.com"
        )

    assert len(items) == 2
    assert all(isinstance(item, LLMExecutiveItem) for item in items)
    assert items[0].name == "Jane Doe"
    assert items[0].title == "CEO"
    assert items[1].title == ""


@pytest.mark.asyncio
async def test_llm_extract_records_never_calls_llm_without_api_key() -> None:
    with patch("scout.core.llm_extract.LLMExtractionStrategy.extract") as mock_extract:
        items = await llm_extract_records("some content", "products", "")

    mock_extract.assert_not_called()
    assert items == []


@pytest.mark.asyncio
async def test_llm_extract_records_never_calls_llm_with_empty_content() -> None:
    with patch("scout.core.llm_extract.LLMExtractionStrategy.extract") as mock_extract:
        items = await llm_extract_records("   \n  ", "products", "fake-key")

    mock_extract.assert_not_called()
    assert items == []


@pytest.mark.asyncio
async def test_llm_extract_records_drops_invalid_items_without_fabricating() -> None:
    def _fake(url, ix, html):
        return [
            {"error": False},  # missing required "name" — invalid, must be dropped
            {"name": "Real Product", "error": False},
            {"error": True, "content": "some LLM error"},  # error block — must be dropped
        ]

    with patch("scout.core.llm_extract.LLMExtractionStrategy.extract", side_effect=_fake):
        items = await llm_extract_records("content", "products", "fake-key")

    assert len(items) == 1
    assert items[0].name == "Real Product"


@pytest.mark.asyncio
async def test_llm_extract_records_returns_empty_on_llm_exception() -> None:
    with patch(
        "scout.core.llm_extract.LLMExtractionStrategy.extract",
        side_effect=RuntimeError("network boom"),
    ):
        items = await llm_extract_records("content", "products", "fake-key")

    assert items == []


@pytest.mark.asyncio
async def test_llm_extract_records_returns_empty_on_non_list_response() -> None:
    with patch(
        "scout.core.llm_extract.LLMExtractionStrategy.extract",
        return_value={"not": "a list"},
    ):
        items = await llm_extract_records("content", "products", "fake-key")

    assert items == []
