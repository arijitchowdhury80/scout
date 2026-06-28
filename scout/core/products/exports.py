"""Local product record export adapters."""

from __future__ import annotations

import csv
import json
import logging
import sqlite3
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from scout.core.types import AlgoliaProductRecord

logger = logging.getLogger(__name__)

_CSV_FIELDS = [
    "objectID",
    "name",
    "url",
    "brand",
    "price",
    "currency",
    "image",
    "categories",
    "source_url",
    "citations",
    "completeness_score",
]


class ProductExportFormat(str, Enum):
    """Supported local product export formats."""

    JSON = "json"
    JSONL = "jsonl"
    CSV = "csv"
    SQLITE = "sqlite"


class ProductExportRequest(BaseModel):
    """Product export request boundary."""

    records: list[AlgoliaProductRecord] = Field(default_factory=list)
    output_dir: Path
    formats: list[ProductExportFormat] = Field(default_factory=lambda: [ProductExportFormat.JSONL])
    basename: str = "products"
    sqlite_table: str = "products"


class ProductExportResult(BaseModel):
    """Product export result boundary."""

    record_count: int
    files: dict[str, Path] = Field(default_factory=dict)


def export_product_records(request: ProductExportRequest) -> ProductExportResult:
    """Export product records to the requested local formats."""
    try:
        request.output_dir.mkdir(parents=True, exist_ok=True)
        files: dict[str, Path] = {}
        for export_format in request.formats:
            files[export_format.value] = _write_format(request, export_format)
        logger.info(
            "export_product_records | complete | records=%d | formats=%s",
            len(request.records),
            ",".join(item.value for item in request.formats),
        )
        return ProductExportResult(record_count=len(request.records), files=files)
    except Exception:
        logger.exception(
            "export_product_records | failed | output_dir=%s | formats=%s",
            request.output_dir,
            ",".join(item.value for item in request.formats),
        )
        raise


def _write_format(request: ProductExportRequest, export_format: ProductExportFormat) -> Path:
    """Dispatch one export format."""
    if export_format is ProductExportFormat.JSON:
        return _write_json(request)
    if export_format is ProductExportFormat.JSONL:
        return _write_jsonl(request)
    if export_format is ProductExportFormat.CSV:
        return _write_csv(request)
    return _write_sqlite(request)


def _write_json(request: ProductExportRequest) -> Path:
    """Write records as a JSON list."""
    path = request.output_dir / f"{request.basename}.json"
    path.write_text(json.dumps(_record_dicts(request), indent=2), encoding="utf-8")
    return path


def _write_jsonl(request: ProductExportRequest) -> Path:
    """Write records as newline-delimited JSON."""
    path = request.output_dir / f"{request.basename}.jsonl"
    lines = [json.dumps(record, sort_keys=True) for record in _record_dicts(request)]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return path


def _write_csv(request: ProductExportRequest) -> Path:
    """Write records as flattened CSV."""
    path = request.output_dir / f"{request.basename}.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(_csv_rows(request))
    return path


def _write_sqlite(request: ProductExportRequest) -> Path:
    """Write records into a SQLite table."""
    path = request.output_dir / f"{request.basename}.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute(_sqlite_schema(request.sqlite_table))
        conn.executemany(_sqlite_insert(request.sqlite_table), _csv_rows(request))
    return path


def _record_dicts(request: ProductExportRequest) -> list[dict[str, object]]:
    """Return JSON-safe product records."""
    return [record.model_dump(mode="json", by_alias=True) for record in request.records]


def _csv_rows(request: ProductExportRequest) -> list[dict[str, object]]:
    """Return flattened rows for CSV and SQLite."""
    return [_flatten_record(record) for record in request.records]


def _flatten_record(record: AlgoliaProductRecord) -> dict[str, object]:
    """Flatten one product record for tabular sinks."""
    data = record.model_dump(mode="json", by_alias=True)
    raw_source = data.get("_source")
    source: dict[str, object] = raw_source if isinstance(raw_source, dict) else {}
    return {
        "objectID": data.get("objectID", ""),
        "name": data.get("name", ""),
        "url": data.get("url", ""),
        "brand": data.get("brand", ""),
        "price": data.get("price"),
        "currency": data.get("currency", ""),
        "image": data.get("image", ""),
        "categories": json.dumps(data.get("categories", [])),
        "source_url": source.get("category_url") or source.get("url") or "",
        "citations": json.dumps(data.get("citations", [])),
        "completeness_score": data.get("completeness_score", 0.0),
    }


def _sqlite_schema(table_name: str) -> str:
    """Return SQLite schema SQL for product export rows."""
    return f"""
    create table if not exists {table_name} (
      objectID text primary key,
      name text,
      url text,
      brand text,
      price real,
      currency text,
      image text,
      categories text,
      source_url text,
      citations text,
      completeness_score real
    )
    """


def _sqlite_insert(table_name: str) -> str:
    """Return SQLite insert SQL for product export rows."""
    fields = ", ".join(_CSV_FIELDS)
    placeholders = ", ".join(f":{field}" for field in _CSV_FIELDS)
    return f"insert or replace into {table_name} ({fields}) values ({placeholders})"
