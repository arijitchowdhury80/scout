"""Opt-in live product crawl examples for real retailer sites.

Run with:
SCOUT_RUN_LIVE_PRODUCT_TESTS=1 python3 -m pytest tests/integration/test_product_sites_live.py -v -m integration
"""

# Scenario list:
# - Lacoste men polos category yields live JSON-LD product records and artifacts
# - Estee Lauder skin-care category writes artifacts but currently xfails when Akamai blocks detail pages
# - Live tests are skipped by default and require SCOUT_RUN_LIVE_PRODUCT_TESTS=1
#
# Validation risk surface:
# - Proves Scout can crawl at least one real JS retail category and write Algolia records.
# - Does not prove every retailer can bypass anti-bot controls.
# - Estee Lauder remains a known anti-bot hardening target.

from __future__ import annotations

import os
from pathlib import Path

import pytest

from scout.core.modes.products import products
from scout.core.types import ProductCrawlRequest


pytestmark = pytest.mark.integration


def _live_enabled() -> bool:
    return os.getenv("SCOUT_RUN_LIVE_PRODUCT_TESTS") == "1"


@pytest.mark.skipif(
    not _live_enabled(), reason="Set SCOUT_RUN_LIVE_PRODUCT_TESTS=1 to run live retailer crawls"
)
@pytest.mark.asyncio
async def test_lacoste_men_polos_live_writes_algolia_records(tmp_path: Path) -> None:
    resp = await products(
        ProductCrawlRequest(
            query="men polos",
            start_url="https://www.lacoste.com/us/lacoste/men/clothing/polos",
            limit_per_category=2,
            max_categories=2,
            max_products=2,
            output_dir=str(tmp_path / "lacoste-men-polos"),
            persist=True,
            use_js=True,
            timeout_ms=60000,
        )
    )

    assert resp.success is True
    assert resp.total_records >= 1
    assert Path(resp.files.products_json).exists()
    assert Path(resp.files.products_ndjson).exists()
    record = resp.records[0]
    assert record.name
    assert record.brand.lower() == "lacoste"
    assert record.url.startswith("https://www.lacoste.com/")
    assert record.source.extractor == "jsonld"


@pytest.mark.skipif(
    not _live_enabled(), reason="Set SCOUT_RUN_LIVE_PRODUCT_TESTS=1 to run live retailer crawls"
)
@pytest.mark.asyncio
async def test_estee_lauder_skin_care_live_documents_blocking_or_records(tmp_path: Path) -> None:
    resp = await products(
        ProductCrawlRequest(
            query="skin care",
            start_url="https://www.esteelauder.com/skin-care",
            limit_per_category=1,
            max_categories=1,
            max_products=1,
            output_dir=str(tmp_path / "estee-lauder-skin-care"),
            persist=True,
            use_js=True,
            stealth=True,
            timeout_ms=60000,
        )
    )

    assert resp.success is True
    assert Path(resp.files.products_json).exists()
    if resp.total_records == 0:
        pytest.xfail(
            "Estee Lauder product detail pages are currently blocked by Akamai in live runs."
        )
    assert "access denied" not in resp.records[0].name.lower()
