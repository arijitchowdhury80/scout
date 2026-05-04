"""Contract tests — verify Pydantic model boundaries hold across all Scout endpoints.

These tests prove that each response model can be constructed from realistic
data and that required fields are present, optional fields default correctly,
and nested model references (e.g. ScrapeResponse.metadata: ScoutMetadata) are
properly typed. A downstream module (PRISM) should be able to trust these
contracts without reading Scout internals.
"""
import pytest
from pydantic import ValidationError

from scout.core.types import (
    ScoutMetadata,
    ScrapeResponse,
    CrawlPage,
    CrawlResponse,
    ExtractResponse,
    MapResponse,
    ScreenshotResponse,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _meta(url: str = "https://example.com") -> ScoutMetadata:
    return ScoutMetadata(url=url, crawled_at="2026-05-03T10:00:00Z")


# ---------------------------------------------------------------------------
# ScrapeResponse contracts
# ---------------------------------------------------------------------------

def test_scrape_response_metadata_is_scout_metadata():
    resp = ScrapeResponse(
        success=True, url="https://example.com",
        markdown="# Hello", metadata=_meta(), duration_ms=500,
    )
    assert isinstance(resp.metadata, ScoutMetadata)


def test_scrape_response_requires_metadata():
    with pytest.raises(ValidationError):
        ScrapeResponse(success=True, url="https://example.com", duration_ms=100)  # type: ignore


def test_scrape_response_requires_duration_ms():
    with pytest.raises(ValidationError):
        ScrapeResponse(success=True, url="https://example.com", metadata=_meta())  # type: ignore


def test_scrape_response_links_is_list_of_str():
    resp = ScrapeResponse(
        success=True, url="https://example.com",
        links=["https://a.com", "https://b.com"],
        metadata=_meta(), duration_ms=100,
    )
    assert all(isinstance(link, str) for link in resp.links)


def test_scrape_response_failure_shape_has_error_field():
    resp = ScrapeResponse(
        success=False, url="https://example.com",
        error="timeout", metadata=_meta(), duration_ms=100,
    )
    assert resp.error == "timeout"
    assert resp.markdown == ""


# ---------------------------------------------------------------------------
# CrawlResponse + CrawlPage contracts
# ---------------------------------------------------------------------------

def test_crawl_response_pages_are_crawl_page_instances():
    page = CrawlPage(url="https://example.com/a", metadata=_meta("https://example.com/a"), success=True)
    resp = CrawlResponse(
        success=True, start_url="https://example.com",
        pages=[page], total_pages=1, duration_ms=800,
    )
    assert isinstance(resp.pages[0], CrawlPage)


def test_crawl_response_total_pages_matches_pages_list():
    pages = [
        CrawlPage(url=f"https://example.com/{i}", metadata=_meta(f"https://example.com/{i}"), success=True)
        for i in range(3)
    ]
    resp = CrawlResponse(
        success=True, start_url="https://example.com",
        pages=pages, total_pages=3, duration_ms=1200,
    )
    assert resp.total_pages == len(resp.pages)


def test_crawl_page_failed_page_has_error():
    page = CrawlPage(
        url="https://example.com/404",
        metadata=_meta("https://example.com/404"),
        success=False,
        error="404 Not Found",
    )
    assert page.success is False
    assert page.error == "404 Not Found"
    assert page.markdown == ""


def test_crawl_response_empty_pages_on_failure():
    resp = CrawlResponse(
        success=False, start_url="https://example.com",
        pages=[], total_pages=0, error="DNS failure", duration_ms=50,
    )
    assert resp.pages == []
    assert resp.total_pages == 0


# ---------------------------------------------------------------------------
# ExtractResponse contracts
# ---------------------------------------------------------------------------

def test_extract_response_data_is_dict():
    resp = ExtractResponse(
        success=True, url="https://example.com",
        data={"ceo": "Jane Smith", "founded": 2010},
        metadata=_meta(), duration_ms=2000,
    )
    assert isinstance(resp.data, dict)
    assert resp.data["ceo"] == "Jane Smith"


def test_extract_response_data_defaults_to_empty_dict():
    resp = ExtractResponse(
        success=True, url="https://example.com",
        metadata=_meta(), duration_ms=100,
    )
    assert resp.data == {}


def test_extract_response_includes_markdown_fallback():
    resp = ExtractResponse(
        success=True, url="https://example.com",
        markdown="# Page content", metadata=_meta(), duration_ms=100,
    )
    assert resp.markdown == "# Page content"


# ---------------------------------------------------------------------------
# MapResponse contracts
# ---------------------------------------------------------------------------

def test_map_response_urls_is_list_of_str():
    resp = MapResponse(
        success=True, start_url="https://example.com",
        urls=["https://example.com/a", "https://example.com/b"],
        total=2, duration_ms=300,
    )
    assert all(isinstance(u, str) for u in resp.urls)


def test_map_response_total_reflects_url_count():
    resp = MapResponse(
        success=True, start_url="https://example.com",
        urls=["https://example.com/a"],
        total=1, duration_ms=200,
    )
    assert resp.total == 1


# ---------------------------------------------------------------------------
# ScreenshotResponse contracts
# ---------------------------------------------------------------------------

def test_screenshot_response_requires_width_and_height():
    with pytest.raises(ValidationError):
        ScreenshotResponse(success=True, url="https://example.com", duration_ms=100)  # type: ignore


def test_screenshot_response_base64_defaults_to_empty():
    resp = ScreenshotResponse(
        success=False, url="https://example.com",
        width=1280, height=800, error="timeout", duration_ms=100,
    )
    assert resp.screenshot_base64 == ""


def test_screenshot_response_success_has_base64():
    resp = ScreenshotResponse(
        success=True, url="https://example.com",
        screenshot_base64="iVBORw0KGgo=",
        width=1280, height=800, duration_ms=1000,
    )
    assert resp.screenshot_base64 == "iVBORw0KGgo="


# ---------------------------------------------------------------------------
# ScoutMetadata contracts
# ---------------------------------------------------------------------------

def test_metadata_is_frozen():
    meta = _meta()
    with pytest.raises(Exception):
        meta.title = "should fail"  # type: ignore


def test_metadata_word_count_and_token_estimate_are_ints():
    meta = ScoutMetadata(
        url="https://example.com", crawled_at="2026-05-03T10:00:00Z",
        word_count=500, token_estimate=375,
    )
    assert isinstance(meta.word_count, int)
    assert isinstance(meta.token_estimate, int)
