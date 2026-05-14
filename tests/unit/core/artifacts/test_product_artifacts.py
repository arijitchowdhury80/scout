"""Tests for durable product run artifacts."""

# Scenario list:
# - product runs create a discoverable run folder
# - Algolia JSON and NDJSON files are written
# - manifest/report/settings files are written
# - _source provenance survives JSON serialization

import json

from scout.core.artifacts import write_product_artifacts
from scout.core.types import (
    AlgoliaProductRecord,
    BlockedPage,
    ProductArtifactFiles,
    ProductCrawlRequest,
    ProductSource,
)


def test_write_product_artifacts_creates_discoverable_run_folder(tmp_path) -> None:
    req = ProductCrawlRequest(query="men shirts", site="shop.example.com", output_dir=str(tmp_path))
    record = AlgoliaProductRecord(
        objectID="abc123",
        name="Oxford Shirt",
        url="https://shop.example.com/products/oxford-shirt",
        categories=["Men", "Shirts"],
        hierarchicalCategories={"lvl0": "Men", "lvl1": "Men > Shirts"},
        source=ProductSource(
            url="https://shop.example.com/products/oxford-shirt",
            extractor="jsonld",
        ),
        completeness_score=0.75,
    )

    files = write_product_artifacts(
        req=req,
        records=[record],
        categories=["Men > Shirts"],
        discovered_urls=["https://shop.example.com/products/oxford-shirt"],
        raw_products=[record.model_dump(mode="json", by_alias=True)],
        blocked_pages=[
            BlockedPage(
                url="https://shop.example.com/products/blocked",
                reason="access_denied",
                category_name="Men Shirts",
                category_url="https://shop.example.com/collections/men-shirts",
            )
        ],
        duration_ms=42,
    )

    assert isinstance(files, ProductArtifactFiles)
    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "algolia" / "products.json").exists()
    assert (tmp_path / "algolia" / "products.ndjson").exists()
    assert (tmp_path / "report.md").exists()

    products = json.loads((tmp_path / "algolia" / "products.json").read_text())
    assert products[0]["objectID"] == "abc123"
    assert products[0]["_source"]["extractor"] == "jsonld"
    assert files.blocked_pages_json.endswith("blocked_pages.json")
    blocked = json.loads((tmp_path / "blocked_pages.json").read_text())
    assert blocked["total"] == 1
    assert blocked["blocked_pages"][0]["reason"] == "access_denied"
