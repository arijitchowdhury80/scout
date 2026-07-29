"""Tests for PDF routing in extract mode — FX-11 Build 1.

Scope note: extract() on a PDF URL returns the extracted PDF text as
markdown so the call succeeds instead of failing (Crawl4AI's browser can't
usefully render a PDF). Running the LLM/CSS extraction_schema *against*
that text is out of scope for this fix — the request's schema/instruction
fields are ignored for PDF URLs, and `data` is returned empty.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from scout.core.modes.extract import extract
from scout.core.types import ExtractRequest

FIXTURE = Path(__file__).parent.parent.parent.parent / "fixtures" / "sample.pdf"


@pytest.mark.asyncio
async def test_extract_pdf_url_returns_text_without_crawling():
    pdf_bytes = FIXTURE.read_bytes()

    with (
        patch("scout.core.modes.extract.fetch_pdf_bytes", new=AsyncMock(return_value=pdf_bytes)),
        patch("scout.core.modes.extract.AsyncWebCrawler") as MockCrawler,
    ):
        req = ExtractRequest(url="https://example.com/sample.pdf")
        resp = await extract(req, llm_api_key="")

        MockCrawler.assert_not_called()

    assert resp.success is True
    assert "Hello Scout PDF" in resp.markdown
    assert resp.error == ""


@pytest.mark.asyncio
async def test_extract_pdf_url_download_failure_returns_error_not_crash():
    with patch(
        "scout.core.modes.extract.fetch_pdf_bytes",
        new=AsyncMock(side_effect=RuntimeError("timeout")),
    ):
        req = ExtractRequest(url="https://example.com/missing.pdf")
        resp = await extract(req, llm_api_key="")

    assert resp.success is False
    assert "timeout" in resp.error
