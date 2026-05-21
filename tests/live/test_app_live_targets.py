from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright


pytestmark = pytest.mark.live

PRODUCT_TARGETS = [
    ("Estée Lauder", "https://www.esteelauder.com/products/681/product-catalog/skin-care"),
    ("Lacoste", "https://www.lacoste.com/us/lacoste/men/clothing/polos"),
    ("Nike", "https://www.nike.com/w/mens-shirts-tops-9om13znik1"),
    ("L.L.Bean", "https://www.llbean.com/llb/shop/502859"),
    ("Patagonia", "https://www.patagonia.com/shop/mens/tops"),
    ("Home Depot", "https://www.homedepot.com/b/Tools/N-5yc1vZc1xy"),
]

INTELLIGENCE_TARGETS = [
    ("company", "Algolia", "https://www.algolia.com/"),
    ("company", "Constructor", "https://constructor.com/"),
    ("company", "Adobe", "https://www.adobe.com/"),
    ("company", "Home Depot", "https://www.homedepot.com/"),
    ("company", "Nike", "https://www.nike.com/"),
    ("company", "British Airways", "https://www.britishairways.com/"),
    ("company", "Estée Lauder", "https://www.esteelauder.com/"),
    ("prism", "Algolia", "https://www.algolia.com/"),
    ("prism", "Constructor", "https://constructor.com/"),
    ("prism", "Adobe", "https://www.adobe.com/"),
    ("prism", "Home Depot", "https://www.homedepot.com/"),
    ("prism", "Nike", "https://www.nike.com/"),
    ("prism", "British Airways", "https://www.britishairways.com/"),
    ("prism", "Estée Lauder", "https://www.esteelauder.com/"),
    ("careers", "Algolia", "https://www.algolia.com/careers/"),
    ("careers", "Constructor", "https://constructor.com/careers/"),
    ("careers", "Adobe", "https://careers.adobe.com/"),
    ("careers", "Home Depot", "https://careers.homedepot.com/"),
    ("careers", "Nike", "https://jobs.nike.com/"),
    ("careers", "British Airways", "https://careers.ba.com/"),
    ("careers", "Estée Lauder", "https://www.elcompanies.com/en/careers"),
    ("news", "Algolia", "https://www.algolia.com/blog/"),
    ("news", "Constructor", "https://constructor.com/blog"),
    ("news", "Adobe", "https://news.adobe.com/"),
    ("news", "Home Depot", "https://corporate.homedepot.com/newsroom"),
    ("news", "Nike", "https://about.nike.com/en/newsroom"),
    ("news", "British Airways", "https://mediacentre.britishairways.com/"),
    ("news", "Estée Lauder", "https://www.elcompanies.com/en/news-and-media"),
    ("investor", "Adobe", "https://www.adobe.com/investor-relations.html"),
    ("investor", "Home Depot", "https://ir.homedepot.com/"),
    ("investor", "Estée Lauder", "https://www.elcompanies.com/en/investors"),
    ("investor", "British Airways", "https://www.iairgroup.com/en/investors-and-shareholders"),
]


@pytest.fixture(scope="module")
def scout_server() -> Iterator[str]:
    if os.getenv("SCOUT_LIVE_TESTS") != "1":
        pytest.skip("Set SCOUT_LIVE_TESTS=1 to run mandatory live website UI tests")
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "scout.cli", "serve", "--host", "127.0.0.1", "--port", str(port)],
        cwd=Path(__file__).parents[2],
        env={**os.environ, "SCOUT_LIVE_TESTS": "1", "SCOUT_DISABLE_NATIVE_PICKER": "1"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_for_health(base_url)
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture()
def page(scout_server: str) -> Iterator[Page]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        context.set_default_timeout(180000)
        browser_page = context.new_page()
        errors: list[str] = []
        browser_page.on(
            "console",
            lambda msg: errors.append(msg.text) if msg.type == "error" else None,
        )
        browser_page.goto(f"{scout_server}/app")
        browser_page.wait_for_load_state("networkidle")
        browser_page.console_errors = errors  # type: ignore[attr-defined]
        yield browser_page
        browser.close()


@pytest.mark.parametrize(("company", "url"), PRODUCT_TARGETS)
def test_product_targets_run_from_ui(page: Page, tmp_path: Path, company: str, url: str) -> None:
    result = _run_ui_workflow(
        page=page,
        use_case="products",
        mode="auto",
        company=company,
        url=url,
        output_dir=tmp_path / _slug(company) / "products",
    )

    assert result["run_status"] in {"success", "blocked_with_evidence"}, result
    assert result["record_count"] > 0 or result["blocked_count"] > 0, result
    assert result["source_count"] > 0 or result["blocked_count"] > 0, result
    assert result["run_id"], result
    assert result["artifact_count"] > 0, result
    if result["record_count"] > 0:
        assert result["citation_count"] > 0 or result["source_count"] > 0, result


@pytest.mark.parametrize(("use_case", "company", "url"), INTELLIGENCE_TARGETS)
def test_intelligence_targets_run_from_ui(
    page: Page, tmp_path: Path, use_case: str, company: str, url: str
) -> None:
    result = _run_ui_workflow(
        page=page,
        use_case=use_case,
        mode="auto",
        company=company,
        url=url,
        output_dir=tmp_path / _slug(company) / use_case,
    )

    assert result["run_status"] == "success", result
    assert result["record_count"] > 0, result
    assert result["source_count"] > 0, result
    assert result["citation_count"] > 0, result
    assert result["run_id"], result
    assert result["artifact_count"] > 0, result


def test_estee_lauder_hard_site_modes_from_ui(page: Page, tmp_path: Path) -> None:
    results = [
        _run_ui_workflow(
            page=page,
            use_case="products",
            mode=mode,
            company="Estée Lauder",
            url="https://www.esteelauder.com/products/681/product-catalog/skin-care",
            output_dir=tmp_path / "estee-lauder-hard-site" / mode,
        )
        for mode in ["auto", "crawl4ai", "browser"]
    ]

    for result in results:
        assert result["run_status"] in {"success", "blocked_with_evidence"}, result
        assert result["record_count"] > 0 or result["blocked_count"] > 0, result
        assert result["record_count"] > 0 or result["blocked_count"] > 0, result
        assert result["run_id"], result
        assert result["artifact_count"] > 0, result


def _run_ui_workflow(
    page: Page,
    use_case: str,
    mode: str,
    company: str,
    url: str,
    output_dir: Path,
) -> dict[str, object]:
    page.locator("#clearRun").click()
    page.locator("#startExecution").wait_for(state="visible", timeout=30000)
    page.wait_for_function(
        "() => !document.querySelector('#startExecution')?.disabled",
        timeout=30000,
    )
    page.locator("#useCase").select_option(use_case)
    page.locator(f"[data-mode='{mode}']").click()
    page.locator("#targetUrl").fill(url)
    output_dir.mkdir(parents=True, exist_ok=True)
    page.locator("#workdir").fill(str(output_dir))
    page.locator("#startExecution").click()
    page.locator("#livePanel").wait_for(state="visible", timeout=180000)
    page.wait_for_function(
        "() => /complete|failed|cancelled/i.test(document.querySelector('#runStateBadge')?.textContent || '')",
        timeout=180000,
    )
    status_text = page.locator("#runStateBadge").inner_text()
    page.locator("[data-panel='recordsPanel']").click()
    page.locator("[data-panel='sourcesPanel']").click()
    page.locator("[data-panel='blockedPanel']").click()
    page.locator("[data-panel='artifactsPanel']").click()
    result = page.evaluate(
        """({ company, useCase, url, mode, statusText }) => {
            const runId = document.querySelector('#activeRunId')?.textContent?.trim() || '';
            const recordRows = [...document.querySelectorAll('#recordsTable tbody tr')]
              .filter((row) => !/No records/i.test(row.textContent || ''));
            const sourcesText = document.querySelector('#sourcesPanel')?.textContent || '';
            const blockedText = document.querySelector('#blockedPanel')?.textContent || '';
            const artifactsText = document.querySelector('#artifactsPanel')?.textContent || '';
            const sourceRows = [...document.querySelectorAll('#sourcesPanel tbody tr')];
            const blockedRows = [...document.querySelectorAll('#blockedPanel tbody tr')];
            const citationCount = recordRows.reduce((total, row) => total + (/Citation|source|Listing|Detail/i.test(row.textContent || '') ? 1 : 0), 0);
            return {
              run_id: runId,
              company,
              use_case: useCase,
              url,
              mode,
              status_text: statusText,
              run_status: /complete/i.test(statusText) ? 'success' : (/blocked|fallback|access|timeout/i.test(blockedText) ? 'blocked_with_evidence' : 'failed'),
              record_count: recordRows.length,
              source_count: sourceRows.length || (/https?:\\/\\//i.test(sourcesText) ? 1 : 0),
              blocked_count: blockedRows.length || (/blocked|access|fallback/i.test(blockedText) ? 1 : 0),
              citation_count: citationCount,
              artifact_count: (/manifest|records|source|blocked|report|output/i.test(artifactsText) ? 1 : 0),
              artifact_summary: artifactsText.replace(/\\s+/g, ' ').trim().slice(0, 500)
            };
        }""",
        {
            "company": company,
            "useCase": use_case,
            "url": url,
            "mode": mode,
            "statusText": status_text,
        },
    )
    assert not page.console_errors  # type: ignore[attr-defined]
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "ui-live-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def _slug(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_health(base_url: str) -> None:
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=2) as resp:
                if resp.status == 200:
                    return
        except OSError:
            time.sleep(0.25)
    raise RuntimeError("Scout server did not become healthy")
