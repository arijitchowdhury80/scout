"""Tests for scout.core.pdf — FX-11 Build 1 real PDF extraction."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from scout.core.pdf import extract_pdf_text, fetch_pdf_bytes, looks_like_pdf_url
from scout.core.types import PdfMetadata

FIXTURE = Path(__file__).parent.parent.parent / "fixtures" / "sample.pdf"


def test_looks_like_pdf_url_true_for_pdf_extension():
    assert looks_like_pdf_url("https://example.com/whitepaper.pdf") is True


def test_looks_like_pdf_url_true_with_query_string():
    assert looks_like_pdf_url("https://example.com/report.pdf?download=1") is True


def test_looks_like_pdf_url_false_for_html_page():
    assert looks_like_pdf_url("https://example.com/about") is False


def test_extract_pdf_text_returns_markdown_and_metadata():
    pdf_bytes = FIXTURE.read_bytes()

    markdown, metadata = extract_pdf_text(pdf_bytes)

    assert "Hello Scout PDF" in markdown
    assert isinstance(metadata, PdfMetadata)
    assert metadata.page_count == 1
    assert metadata.title == "Scout PDF Fixture"
    assert metadata.encrypted is False


def test_extract_pdf_text_raises_on_garbage_bytes():
    with pytest.raises(Exception):
        extract_pdf_text(b"not a pdf at all")


@pytest.mark.asyncio
async def test_fetch_pdf_bytes_downloads_content(monkeypatch):
    fixture_bytes = FIXTURE.read_bytes()

    class _MockResponse:
        content = fixture_bytes

        def raise_for_status(self) -> None:
            return None

    class _MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url: str):
            assert url == "https://example.com/sample.pdf"
            return _MockResponse()

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: _MockClient())

    result = await fetch_pdf_bytes("https://example.com/sample.pdf", timeout_ms=5000)

    assert result == fixture_bytes
