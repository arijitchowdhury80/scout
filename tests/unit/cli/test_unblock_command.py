"""The `scout unblock` glue: the CDP bridge adapter must delegate open/capture
to the injected service (so the engine flow stays decoupled from the api layer),
and the command must be registered.
"""

import asyncio

from scout.cli import _CDPBridge, _write_unblock_artifacts, app
from scout.core.human_assisted import HumanAssistedOutcome


class FakeService:
    def __init__(self) -> None:
        self.opened_url = None
        self.captured_url = None

    async def open_browser(self, req):
        self.opened_url = req.url
        return None

    async def capture_active_tab(self, url):
        self.captured_url = url
        return object()

    async def navigate_capture(self, url):
        self.navigated_url = url
        return object()


def test_bridge_open_delegates_with_url() -> None:
    svc = FakeService()
    asyncio.run(_CDPBridge(svc).open("https://zillow.com/x"))
    assert svc.opened_url == "https://zillow.com/x"


def test_bridge_capture_delegates_with_url() -> None:
    svc = FakeService()
    asyncio.run(_CDPBridge(svc).capture("https://zillow.com/x"))
    assert svc.captured_url == "https://zillow.com/x"


def test_bridge_navigate_capture_delegates_with_url() -> None:
    svc = FakeService()
    asyncio.run(_CDPBridge(svc).navigate_capture("https://zillow.com/homedetails/1/"))
    assert svc.navigated_url == "https://zillow.com/homedetails/1/"


def test_unblock_command_is_registered() -> None:
    names = {c.name or c.callback.__name__ for c in app.registered_commands}
    assert "unblock" in names


def test_unblock_artifacts_include_html_and_product_records(tmp_path) -> None:
    outcome = HumanAssistedOutcome(
        status="cleared",
        final_url="https://www.esteelauder.com/products/681/product-catalog/skin-care",
        title="Skin Care",
        markdown="Advanced Night Repair Serum $85",
        html="""
        <div class="product-brief"
             data-product-name="Advanced Night Repair Serum"
             data-brand="Estée Lauder">
          <a href="/product/681/141225/product-catalog/skincare/advanced-night-repair-serum">
            <img src="/media/anr.jpg" alt="">
          </a>
          <span>$85.00</span>
        </div>
        """,
    )

    summary = _write_unblock_artifacts(outcome, tmp_path)

    assert (tmp_path / "capture.md").read_text() == "Advanced Night Repair Serum $85"
    assert "product-brief" in (tmp_path / "capture.html").read_text()
    assert (tmp_path / "capture.json").exists()
    records = (tmp_path / "product_records.json").read_text()
    assert "Advanced Night Repair Serum" in records
    assert summary["product_record_count"] == 1
