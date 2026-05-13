"""Durable run artifact writers for Scout."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from scout.core.types import (
    AlgoliaProductRecord,
    ProductArtifactFiles,
    ProductCrawlRequest,
)
from scout.core.version import SCOUT_VERSION


def default_run_dir(query: str, site: str) -> Path:
    """Return a discoverable default run directory under the current working dir."""
    slug = _slugify(" ".join(part for part in [site, query] if part) or "scout-run")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return Path.cwd() / "scout-runs" / f"{slug}-{stamp}"


def write_product_artifacts(
    req: ProductCrawlRequest,
    records: list[AlgoliaProductRecord],
    categories: list[str],
    discovered_urls: list[str],
    raw_products: list[dict],
    duration_ms: int,
) -> ProductArtifactFiles:
    """Write product crawl artifacts to a run directory."""
    out_dir = Path(req.output_dir) if req.output_dir else default_run_dir(req.query, req.site)
    raw_dir = out_dir / "raw"
    extracted_dir = out_dir / "extracted"
    algolia_dir = out_dir / "algolia"
    raw_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir.mkdir(parents=True, exist_ok=True)
    algolia_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = out_dir / "manifest.json"
    urls_path = out_dir / "urls.json"
    raw_products_path = extracted_dir / "products.raw.jsonl"
    products_json_path = algolia_dir / "products.json"
    products_ndjson_path = algolia_dir / "products.ndjson"
    settings_path = algolia_dir / "settings.json"
    report_path = out_dir / "report.md"

    manifest = {
        "scout_version": SCOUT_VERSION,
        "query": req.query,
        "site": req.site,
        "start_url": req.start_url,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "duration_ms": duration_ms,
        "total_records": len(records),
        "categories": categories,
    }
    _write_json(manifest_path, manifest)
    _write_json(urls_path, {"urls": discovered_urls, "total": len(discovered_urls)})
    _write_jsonl(raw_products_path, raw_products)
    product_dicts = [record.model_dump(mode="json", by_alias=True) for record in records]
    _write_json(products_json_path, product_dicts)
    _write_jsonl(products_ndjson_path, product_dicts)
    _write_json(settings_path, _algolia_settings())
    report_path.write_text(_report(req, records, categories), encoding="utf-8")

    return ProductArtifactFiles(
        manifest=str(manifest_path),
        urls=str(urls_path),
        raw_products=str(raw_products_path),
        products_json=str(products_json_path),
        products_ndjson=str(products_ndjson_path),
        settings_json=str(settings_path),
        report=str(report_path),
    )


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, values: list[dict]) -> None:
    lines = [json.dumps(value, sort_keys=True) for value in values]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _algolia_settings() -> dict:
    return {
        "searchableAttributes": ["name", "brand", "description", "categories"],
        "attributesForFaceting": [
            "brand",
            "categories",
            "hierarchicalCategories.lvl0",
            "currency",
            "in_stock",
        ],
        "customRanking": ["desc(in_stock)", "asc(price)"],
    }


def _report(
    req: ProductCrawlRequest,
    records: list[AlgoliaProductRecord],
    categories: list[str],
) -> str:
    lines = [
        f"# Scout Product Crawl — {req.query or req.site}",
        "",
        f"- Site: {req.site or req.start_url}",
        f"- Records: {len(records)}",
        f"- Categories: {len(categories)}",
        "",
        "## Output",
        "",
        "- `algolia/products.json`: JSON array for inspection",
        "- `algolia/products.ndjson`: newline-delimited records for bulk import",
        "- `algolia/settings.json`: suggested Algolia index settings",
        "",
    ]
    return "\n".join(lines)


def _slugify(value: str) -> str:
    chars = [ch.lower() if ch.isalnum() else "-" for ch in value]
    slug = "-".join(part for part in "".join(chars).split("-") if part)
    return slug[:80] or "scout-run"
