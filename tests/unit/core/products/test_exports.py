"""Tests for generic product export adapters.

# Scenario list:
# - JSON export writes a valid list of product records
# - JSONL export writes one product record per line
# - CSV export flattens common product fields and preserves citations/source as JSON
# - SQLite export creates a table and inserts product rows
# - empty record lists still create valid artifacts
# - Pydantic contract rejects unsupported export formats
"""

from __future__ import annotations

import csv
import json
import sqlite3

import pytest
from pydantic import ValidationError

from scout.core.products.exports import (
    ProductExportFormat,
    ProductExportRequest,
    export_product_records,
)
from scout.core.types import AlgoliaProductRecord, ProductSource


def _record() -> AlgoliaProductRecord:
    return AlgoliaProductRecord(
        objectID="prod_1",
        name="Advanced Night Repair Serum",
        url="https://shop.example.com/products/advanced-night-repair",
        brand="Estee Lauder",
        image="https://shop.example.com/anr.jpg",
        price=85.0,
        currency="USD",
        categories=["Skin Care"],
        source=ProductSource(
            url="https://shop.example.com/products/advanced-night-repair",
            extractor="listing",
            category_url="https://shop.example.com/skin-care",
            category_name="Skin Care",
        ),
        citations=[
            {
                "source_id": "src_1",
                "source_url": "https://shop.example.com/skin-care",
                "field": "name",
                "claim": "Advanced Night Repair Serum",
                "snippet": "Advanced Night Repair Serum",
                "confidence": 0.75,
            }
        ],
        completeness_score=0.75,
    )


def test_export_product_records_json_writes_record_list(tmp_path) -> None:
    request = ProductExportRequest(
        records=[_record()],
        output_dir=tmp_path,
        formats=[ProductExportFormat.JSON],
    )

    result = export_product_records(request)

    assert result.record_count == 1
    assert result.files["json"].exists()
    data = json.loads(result.files["json"].read_text(encoding="utf-8"))
    assert data[0]["objectID"] == "prod_1"
    assert data[0]["_source"]["category_url"] == "https://shop.example.com/skin-care"


def test_export_product_records_jsonl_writes_one_record_per_line(tmp_path) -> None:
    request = ProductExportRequest(
        records=[_record()],
        output_dir=tmp_path,
        formats=[ProductExportFormat.JSONL],
    )

    result = export_product_records(request)

    lines = result.files["jsonl"].read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["name"] == "Advanced Night Repair Serum"


def test_export_product_records_csv_flattens_common_fields(tmp_path) -> None:
    request = ProductExportRequest(
        records=[_record()],
        output_dir=tmp_path,
        formats=[ProductExportFormat.CSV],
    )

    result = export_product_records(request)

    rows = list(csv.DictReader(result.files["csv"].open(encoding="utf-8")))
    assert rows[0]["objectID"] == "prod_1"
    assert rows[0]["source_url"] == "https://shop.example.com/skin-care"
    assert json.loads(rows[0]["categories"]) == ["Skin Care"]
    assert json.loads(rows[0]["citations"])[0]["field"] == "name"


def test_export_product_records_sqlite_creates_table_and_rows(tmp_path) -> None:
    request = ProductExportRequest(
        records=[_record()],
        output_dir=tmp_path,
        formats=[ProductExportFormat.SQLITE],
        sqlite_table="scout_products",
    )

    result = export_product_records(request)

    with sqlite3.connect(result.files["sqlite"]) as conn:
        row = conn.execute("select objectID, name, source_url from scout_products").fetchone()
    assert row == (
        "prod_1",
        "Advanced Night Repair Serum",
        "https://shop.example.com/skin-care",
    )


def test_export_product_records_empty_records_writes_empty_artifacts(tmp_path) -> None:
    request = ProductExportRequest(
        records=[],
        output_dir=tmp_path,
        formats=[ProductExportFormat.JSON, ProductExportFormat.CSV],
    )

    result = export_product_records(request)

    assert result.record_count == 0
    assert json.loads(result.files["json"].read_text(encoding="utf-8")) == []
    assert "objectID" in result.files["csv"].read_text(encoding="utf-8").splitlines()[0]


def test_product_export_request_rejects_unsupported_format(tmp_path) -> None:
    with pytest.raises(ValidationError):
        ProductExportRequest(
            records=[],
            output_dir=tmp_path,
            formats=["google_sheets"],
        )
