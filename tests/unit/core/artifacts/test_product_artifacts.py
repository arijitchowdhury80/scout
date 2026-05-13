"""Tests for durable product run artifacts."""

import json

from scout.core.artifacts import write_product_artifacts
from scout.core.types import (
    AlgoliaProductRecord,
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
    )

    files = write_product_artifacts(
        req=req,
        records=[record],
        categories=["Men > Shirts"],
        discovered_urls=["https://shop.example.com/products/oxford-shirt"],
        raw_products=[record.model_dump(mode="json", by_alias=True)],
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
