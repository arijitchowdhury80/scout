"""Tests for extract mode — LLM-based structured extraction."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

from crawl4ai.extraction_strategy import ExtractionStrategy

from scout.core.modes.extract import extract
from scout.core.types import ExtractRequest, ExtractResponse


def _make_strategy_mock() -> MagicMock:
    """Return a mock that passes CrawlerRunConfig's isinstance check."""
    return create_autospec(ExtractionStrategy, instance=True)


@pytest.mark.asyncio
async def test_extract_returns_structured_data():
    schema = {"type": "object", "properties": {"name": {"type": "string"}, "ceo": {"type": "string"}}}
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.url = "https://example.com"
    mock_result.markdown = "Nike is led by John Donahoe"
    mock_result.fit_markdown = "Nike is led by John Donahoe"
    mock_result.extracted_content = json.dumps({"name": "Nike", "ceo": "John Donahoe"})
    mock_result.metadata = {"title": "Nike", "description": "", "language": "en"}

    with patch("scout.core.modes.extract.AsyncWebCrawler") as MockCrawler:
        with patch("scout.core.modes.extract.LLMExtractionStrategy", return_value=_make_strategy_mock()):
            instance = AsyncMock()
            instance.arun.return_value = mock_result
            MockCrawler.return_value.__aenter__.return_value = instance

            req = ExtractRequest(
                url="https://example.com",
                **{"schema": schema},
                instruction="Extract company name and CEO",
            )
            resp = await extract(req, llm_api_key="fake-key")

    assert resp.success is True
    assert resp.data.get("name") == "Nike"
    assert resp.data.get("ceo") == "John Donahoe"


@pytest.mark.asyncio
async def test_extract_includes_markdown_fallback():
    schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.url = "https://example.com"
    mock_result.markdown = "Some content"
    mock_result.fit_markdown = "Some content"
    mock_result.extracted_content = json.dumps({"name": "Acme"})
    mock_result.metadata = {"title": "", "description": "", "language": ""}

    with patch("scout.core.modes.extract.AsyncWebCrawler") as MockCrawler:
        with patch("scout.core.modes.extract.LLMExtractionStrategy", return_value=_make_strategy_mock()):
            instance = AsyncMock()
            instance.arun.return_value = mock_result
            MockCrawler.return_value.__aenter__.return_value = instance

            req = ExtractRequest(url="https://example.com", **{"schema": schema}, instruction="Extract")
            resp = await extract(req, llm_api_key="fake-key")

    assert resp.markdown == "Some content"


@pytest.mark.asyncio
async def test_extract_handles_invalid_json_gracefully():
    schema = {"type": "object"}
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.url = "https://example.com"
    mock_result.markdown = "content"
    mock_result.fit_markdown = "content"
    mock_result.extracted_content = "not-valid-json{{{"
    mock_result.metadata = {"title": "", "description": "", "language": ""}

    with patch("scout.core.modes.extract.AsyncWebCrawler") as MockCrawler:
        with patch("scout.core.modes.extract.LLMExtractionStrategy", return_value=_make_strategy_mock()):
            instance = AsyncMock()
            instance.arun.return_value = mock_result
            MockCrawler.return_value.__aenter__.return_value = instance

            req = ExtractRequest(url="https://example.com", **{"schema": schema}, instruction="Extract")
            resp = await extract(req, llm_api_key="fake-key")

    assert resp.success is True
    assert resp.data == {}


@pytest.mark.asyncio
async def test_extract_handles_exception():
    schema = {"type": "object"}
    with patch("scout.core.modes.extract.AsyncWebCrawler") as MockCrawler:
        MockCrawler.return_value.__aenter__.side_effect = RuntimeError("LLM timeout")
        req = ExtractRequest(url="https://example.com", **{"schema": schema}, instruction="Extract")
        resp = await extract(req, llm_api_key="fake-key")

    assert resp.success is False
    assert "LLM timeout" in resp.error
