"""Tests for Scout core types — the contract every endpoint fulfils."""

import pytest
from pydantic import ValidationError

from scout.core.types import (
    AlgoliaProductRecord,
    BlockedPage,
    ScoutFormats,
    ScoutMetadata,
    ScrapeRequest,
    ScrapeResponse,
    CrawlRequest,
    CrawlPage,
    CrawlResponse,
    ExtractRequest,
    ExtractResponse,
    MapRequest,
    MapResponse,
    ScreenshotRequest,
    ScreenshotResponse,
    ProductArtifactFiles,
    ProductCrawlRequest,
    ProductCrawlResponse,
    ProductListingCard,
    ProductSource,
)


# --- ScoutMetadata ---


def test_metadata_defaults_are_empty_not_none():
    m = ScoutMetadata(url="https://example.com", crawled_at="2026-05-03T20:00:00Z")
    assert m.title == ""
    assert m.description == ""
    assert m.language == ""
    assert m.word_count == 0
    assert m.token_estimate == 0


def test_metadata_requires_url_and_crawled_at():
    with pytest.raises(ValidationError):
        ScoutMetadata()  # type: ignore


# --- ScrapeRequest ---


def test_scrape_request_defaults():
    req = ScrapeRequest(url="https://example.com")
    assert req.formats == [ScoutFormats.MARKDOWN]
    assert req.use_js is False
    assert req.wait_for == ""
    assert req.timeout_ms == 30000


def test_scrape_request_requires_url():
    with pytest.raises(ValidationError):
        ScrapeRequest()  # type: ignore


# --- ScrapeResponse ---


def test_scrape_response_success_shape():
    meta = ScoutMetadata(url="https://example.com", crawled_at="2026-05-03T20:00:00Z")
    resp = ScrapeResponse(
        success=True,
        url="https://example.com",
        markdown="# Hello",
        metadata=meta,
        duration_ms=500,
    )
    assert resp.success is True
    assert resp.markdown == "# Hello"
    assert resp.raw_html == ""
    assert resp.screenshot_base64 == ""
    assert resp.links == []
    assert resp.error == ""


def test_scrape_response_failure_shape():
    meta = ScoutMetadata(url="https://example.com", crawled_at="2026-05-03T20:00:00Z")
    resp = ScrapeResponse(
        success=False,
        url="https://example.com",
        metadata=meta,
        duration_ms=100,
        error="Connection timeout",
    )
    assert resp.success is False
    assert resp.markdown == ""
    assert resp.error == "Connection timeout"


# --- CrawlRequest ---


def test_crawl_request_defaults():
    req = CrawlRequest(url="https://example.com")
    assert req.max_depth == 2
    assert req.max_pages == 10
    assert req.url_pattern == ""
    assert req.include_external is False
    assert req.use_js is False


# --- CrawlResponse ---


def test_crawl_response_contains_pages():
    meta = ScoutMetadata(url="https://example.com/page", crawled_at="2026-05-03T20:00:00Z")
    page = CrawlPage(
        url="https://example.com/page", markdown="content", metadata=meta, success=True
    )
    resp = CrawlResponse(
        success=True,
        start_url="https://example.com",
        pages=[page],
        total_pages=1,
        duration_ms=1200,
    )
    assert len(resp.pages) == 1
    assert resp.total_pages == 1
    assert resp.pages[0].url == "https://example.com/page"


# --- ExtractRequest ---


def test_extract_request_minimal_valid():
    # url is the only required field; schema, instruction, css_schema all have defaults
    req = ExtractRequest(url="https://example.com")
    assert req.url == "https://example.com"
    assert req.css_schema is None
    assert req.instruction == ""


def test_extract_request_shape():
    req = ExtractRequest(
        url="https://example.com",
        **{"schema": {"type": "object", "properties": {"name": {"type": "string"}}}},
        instruction="Extract the company name",
    )
    assert req.llm_provider == "ollama/llama3.2:3b"
    assert req.use_js is False


# --- ExtractResponse ---


def test_extract_response_data_is_dict():
    meta = ScoutMetadata(url="https://example.com", crawled_at="2026-05-03T20:00:00Z")
    resp = ExtractResponse(
        success=True,
        url="https://example.com",
        data={"name": "Nike", "ceo": "John Donahoe"},
        metadata=meta,
        duration_ms=2000,
    )
    assert resp.data["name"] == "Nike"
    assert resp.markdown == ""


# --- MapRequest ---


def test_map_request_defaults():
    req = MapRequest(url="https://example.com")
    assert req.max_pages == 100
    assert req.url_pattern == ""
    assert req.include_external is False


# --- MapResponse ---


def test_map_response_urls_list():
    resp = MapResponse(
        success=True,
        start_url="https://example.com",
        urls=["https://example.com/about", "https://example.com/careers"],
        total=2,
        duration_ms=800,
    )
    assert len(resp.urls) == 2
    assert resp.total == 2


# --- ScreenshotRequest ---


def test_screenshot_request_defaults():
    req = ScreenshotRequest(url="https://example.com")
    assert req.full_page is True
    assert req.viewport_width == 1280
    assert req.viewport_height == 800
    assert req.use_js is True


# --- ScreenshotResponse ---


def test_screenshot_response_shape():
    resp = ScreenshotResponse(
        success=True,
        url="https://example.com",
        screenshot_base64="iVBORw0KGgo=",
        width=1280,
        height=800,
        duration_ms=1500,
    )
    assert resp.screenshot_base64 == "iVBORw0KGgo="
    assert resp.width == 1280


# --- Products ---


def test_product_crawl_request_defaults():
    req = ProductCrawlRequest(query="men shirts", site="shop.example.com")
    assert req.limit_per_category == 10
    assert req.max_categories == 10
    assert req.max_products == 100
    assert req.output_dir == ""
    assert req.persist is False
    assert req.use_js is True
    assert req.browser_fallback is True
    assert req.browser_fallback_headless is False


def test_algolia_product_record_serializes_source_alias():
    record = AlgoliaProductRecord(
        objectID="abc123",
        name="Oxford Shirt",
        url="https://shop.example.com/products/oxford",
        source=ProductSource(
            url="https://shop.example.com/products/oxford",
            extractor="jsonld",
        ),
        completeness_score=0.75,
    )

    dumped = record.model_dump(mode="json", by_alias=True)
    assert dumped["_source"]["url"] == "https://shop.example.com/products/oxford"
    assert dumped["completeness_score"] == 0.75


def test_product_listing_card_contract_has_category_context():
    card = ProductListingCard(
        url="https://shop.example.com/products/serum",
        name="Serum",
        image="https://shop.example.com/serum.jpg",
        category_url="https://shop.example.com/skin-care",
        category_name="Skin Care",
        price=82.0,
        currency="USD",
    )

    assert card.category_name == "Skin Care"
    assert card.price == 82.0


def test_product_crawl_response_includes_artifact_files():
    resp = ProductCrawlResponse(
        success=True,
        query="men shirts",
        site="shop.example.com",
        start_url="https://shop.example.com",
        records=[],
        total_records=0,
        files=ProductArtifactFiles(manifest="manifest.json", blocked_pages_json="blocked.json"),
        blocked_pages=[
            BlockedPage(
                url="https://shop.example.com/products/serum",
                reason="access_denied",
                category_url="https://shop.example.com/skin-care",
                category_name="Skin Care",
                fallback_attempted=True,
                fallback_used=False,
            )
        ],
        total_blocked_pages=1,
        duration_ms=10,
    )

    assert resp.files.manifest == "manifest.json"
    assert resp.files.blocked_pages_json == "blocked.json"
    assert resp.total_blocked_pages == 1
