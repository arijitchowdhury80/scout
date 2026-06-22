import json

import pytest

from scout.core.platform.types import RunRequest
from scout.core.platform.run import run_use_case


def _records(output_dir) -> list[dict]:
    return json.loads((output_dir / "records.json").read_text())


@pytest.mark.asyncio
async def test_company_run_writes_company_exec_and_social_records(tmp_path) -> None:
    output_dir = tmp_path / "company-run"

    resp = await run_use_case(
        RunRequest(
            use_case="company",
            query="Adobe",
            targets=["https://www.adobe.com"],
            output_dir=str(output_dir),
            mode="auto",
        )
    )

    assert resp.success is True
    records = _records(output_dir)
    assert {record["record_type"] for record in records} >= {
        "company",
        "executive",
        "company_social",
    }
    manifest = json.loads((output_dir / "manifest.json").read_text())
    assert manifest["providers_attempted"][0] == "crawl4ai"
    assert "host_browser" in manifest["providers_attempted"]
    source_pages = json.loads((output_dir / "source_pages.json").read_text())
    assert source_pages[0]["source_id"] == records[0]["citations"][0]["source_id"]
    assert records[0]["citations"][0]["field"] == "website"


@pytest.mark.asyncio
async def test_careers_investor_news_and_research_runs_write_typed_records(tmp_path) -> None:
    cases = {
        "careers": "career_site",
        "investor": "investor_asset",
        "news": "news_signal",
        "research": "research_record",
    }

    for use_case, record_type in cases.items():
        output_dir = tmp_path / use_case
        resp = await run_use_case(
            RunRequest(use_case=use_case, query="Adobe", output_dir=str(output_dir), mode="saved")
        )

        assert resp.success is True
        records = _records(output_dir)
        assert records[0]["record_type"] == record_type
        assert records[0]["citations"]


@pytest.mark.asyncio
async def test_prism_run_composes_company_careers_investor_and_news_records(tmp_path) -> None:
    output_dir = tmp_path / "prism-run"

    resp = await run_use_case(
        RunRequest(use_case="prism", query="Adobe", output_dir=str(output_dir))
    )

    assert resp.success is True
    record_types = {record["record_type"] for record in _records(output_dir)}
    assert {"company", "career_site", "investor_asset", "news_signal"} <= record_types


@pytest.mark.asyncio
async def test_products_run_emits_product_records(tmp_path) -> None:
    output_dir = tmp_path / "products-run"

    resp = await run_use_case(
        RunRequest(
            use_case="products",
            query="top skincare products",
            url="https://www.esteelauder.com/products/681/product-catalog/skin-care",
            output_dir=str(output_dir),
        )
    )

    assert resp.success is True
    records = _records(output_dir)
    assert records[0]["schema_version"].startswith("product.")
    assert records[0]["record_type"] == "product"
    assert records[0]["url"] == "https://www.esteelauder.com/products/681/product-catalog/skin-care"
    assert records[0]["citations"][0]["field"] == "url"
