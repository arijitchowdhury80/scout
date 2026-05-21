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
from playwright.sync_api import Page, expect, sync_playwright


API_KEY = "dev-key"


@pytest.fixture(scope="module")
def scout_server() -> Iterator[str]:
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "scout.cli", "serve", "--host", "127.0.0.1", "--port", str(port)],
        cwd=Path(__file__).parents[2],
        env={**os.environ, "SCOUT_DISABLE_NATIVE_PICKER": "1"},
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
        context.grant_permissions(["clipboard-read", "clipboard-write"], origin=scout_server)
        browser_page = context.new_page()
        console_errors: list[str] = []
        browser_page.on(
            "console",
            lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
        )
        browser_page.goto(f"{scout_server}/app")
        browser_page.wait_for_load_state("networkidle")
        browser_page.console_errors = console_errors  # type: ignore[attr-defined]
        yield browser_page
        browser.close()


def test_app_first_layout_has_setup_live_and_results_surfaces(page: Page) -> None:
    expect(page.locator("body")).to_contain_text("Run Setup")
    expect(page.locator("body")).to_contain_text("Live Execution")
    expect(page.locator("body")).to_contain_text("Results Review")
    expect(page.locator("body")).to_contain_text("Crawl Settings")
    expect(page.locator("#developerDetails")).not_to_have_attribute("open", "")
    expect(page.locator("#livePanel")).to_be_hidden()
    expect(page.locator("#resultsPanel")).to_be_hidden()
    expect(page.locator("#readyPanel")).to_be_visible()
    expect(page.locator("#clearRun")).to_be_visible()


def test_visible_enabled_controls_are_classified(page: Page, tmp_path: Path) -> None:
    """Every visible enabled control must be known to the test harness."""
    controls = page.evaluate(
        """() => {
            const selectorFor = (el) => {
              if (el.id) return `#${el.id}`;
              for (const attr of [
                'data-mode',
                'data-remove-option',
                'data-add-option',
                'data-top-section',
                'data-rail-section',
                'data-panel',
                'data-copy-target'
              ]) {
                if (el.hasAttribute(attr)) return `[${attr}="${el.getAttribute(attr)}"]`;
              }
              if (el.closest('#developerDetails') && el.tagName.toLowerCase() === 'summary') {
                return '#developerDetails summary';
              }
              if (el.getAttribute('href')) return `${el.tagName.toLowerCase()}[href="${el.getAttribute('href')}"]`;
              return el.tagName.toLowerCase();
            };
            return [...document.querySelectorAll('button, a, select, input, summary, [role="tab"], [data-panel]')]
              .filter((el) => {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return style.display !== 'none'
                  && style.visibility !== 'hidden'
                  && rect.width > 0
                  && rect.height > 0;
              })
              .map((el) => ({
                selector: selectorFor(el),
                tag: el.tagName.toLowerCase(),
                type: el.getAttribute('type') || '',
                label: (el.innerText || el.getAttribute('aria-label') || el.getAttribute('title') || el.getAttribute('value') || el.id || '').trim(),
                disabled: Boolean(el.disabled) || el.getAttribute('aria-disabled') === 'true',
                href: el.getAttribute('href') || ''
              }));
        }"""
    )
    classified = []
    failures = []
    for control in controls:
        status = _classify_control(control)
        item = {**control, "coverage": status}
        classified.append(item)
        if status == "fail":
            failures.append(item)

    manifest_path = tmp_path / "control-coverage-manifest.json"
    manifest_path.write_text(json.dumps(classified, indent=2), encoding="utf-8")

    assert not failures, f"Unclassified visible controls: {json.dumps(failures, indent=2)}"


def test_start_execution_shows_active_run_immediately_and_clear_resets(page: Page) -> None:
    page.route(
        "**/app/runs",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "run_id": "app_run_test123",
                    "status": "running",
                    "use_case": "products",
                    "mode": "auto",
                    "target_url": "https://www.esteelauder.com/products/681/product-catalog/skin-care",
                    "events": [
                        {"stage": "queued", "message": "Run created and queued", "level": "info"},
                        {"stage": "discovering", "message": "Discovering URLs", "level": "info"},
                    ],
                    "records": [],
                    "sources": [],
                    "blocked_pages": [],
                    "artifacts": {},
                    "browser_evidence": {},
                }
            ),
        ),
    )
    page.route(
        "**/app/runs/app_run_test123",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "run_id": "app_run_test123",
                    "status": "complete",
                    "use_case": "products",
                    "mode": "auto",
                    "target_url": "https://www.esteelauder.com/products/681/product-catalog/skin-care",
                    "events": [
                        {"stage": "queued", "message": "Run created and queued", "level": "info"},
                        {
                            "stage": "discovering",
                            "message": "Found 48 listing URLs",
                            "level": "info",
                        },
                        {"stage": "complete", "message": "Run completed", "level": "success"},
                    ],
                    "records": [
                        {
                            "objectID": "el-advanced-night-repair",
                            "name": "Advanced Night Repair Serum",
                            "brand": "Estee Lauder",
                            "price": "$130.00",
                            "url": "https://www.esteelauder.com/product/123",
                            "source_type": "Listing",
                            "citations": [
                                {"field": "name", "claim": "Advanced Night Repair Serum"}
                            ],
                        }
                    ],
                    "sources": [
                        {
                            "source_url": "https://www.esteelauder.com/products/681/product-catalog/skin-care",
                            "provider": "browser",
                            "status_code": 200,
                            "confidence": 0.8,
                        }
                    ],
                    "blocked_pages": [
                        {
                            "url": "https://www.esteelauder.com/product/blocked",
                            "reason": "access_denied",
                            "fallback_attempted": True,
                        }
                    ],
                    "artifacts": {"records_json": "/tmp/records.json"},
                    "browser_evidence": {
                        "url": "https://www.esteelauder.com/products/681/product-catalog/skin-care",
                        "title": "Skincare",
                        "note": "Your browser session can view this page; Scout crawler details may differ.",
                    },
                }
            ),
        ),
    )

    page.locator("#targetUrl").fill(
        "https://www.esteelauder.com/products/681/product-catalog/skin-care"
    )
    page.locator("#startExecution").click()

    expect(page.locator("#livePanel")).to_be_visible()
    expect(page.locator("#activeRunId")).to_contain_text("app_run_test123")
    expect(page.locator("#timeline")).to_contain_text("Discovering URLs")
    expect(page.locator("#resultsPanel")).to_be_visible(timeout=10000)
    expect(page.locator("#recordsTable")).to_contain_text("Advanced Night Repair Serum")
    expect(page.locator("#blockedSummary")).to_contain_text("Detail pages blocked")
    expect(page.locator("#browserEvidence")).to_contain_text("Skincare")

    page.locator("#recordsTable tbody tr").first.click()
    expect(page.locator("#detailDrawer")).to_be_visible()
    expect(page.locator("#detailDrawer")).to_contain_text("Selected Record")

    page.locator("#clearRun").click()
    expect(page.locator("#readyPanel")).to_be_visible()
    expect(page.locator("#livePanel")).to_be_hidden()
    expect(page.locator("#resultsPanel")).to_be_hidden()


def test_start_execution_without_target_shows_inline_validation(page: Page) -> None:
    page.locator("#targetUrl").fill("")
    page.locator("#startExecution").click()

    expect(page.locator("#runStatus")).to_contain_text("Enter a Target / Start URL")
    expect(page.locator("#targetUrl")).to_be_focused()
    assert not page.console_errors  # type: ignore[attr-defined]


def test_cancel_run_marks_ui_cancelled(page: Page) -> None:
    page.route(
        "**/app/runs",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "run_id": "app_run_cancel",
                    "status": "running",
                    "use_case": "products",
                    "mode": "auto",
                    "target_url": "https://www.nike.com/",
                    "events": [{"stage": "queued", "message": "Run created", "level": "info"}],
                    "records": [],
                    "sources": [],
                    "blocked_pages": [],
                    "artifacts": {},
                    "browser_evidence": {},
                }
            ),
        ),
    )
    page.route(
        "**/app/runs/app_run_cancel/cancel",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"run_id": "app_run_cancel", "status": "cancelled"}),
        ),
    )

    page.locator("#targetUrl").fill("https://www.nike.com/")
    page.locator("#startExecution").click()
    page.locator("#cancelRun").click()

    expect(page.locator("#runStateBadge")).to_contain_text("cancelled")


def test_developer_details_copy_and_crawl_settings_restore(page: Page) -> None:
    page.locator("[data-remove-option='delay_seconds']").click()
    expect(page.locator("[data-option-chip='delay_seconds']")).to_have_count(0)
    page.locator("#addOption").click()
    page.locator("[data-add-option='delay_seconds']").click()
    expect(page.locator("[data-option-chip='delay_seconds']")).to_contain_text("Delay")

    page.locator("#developerDetails summary").click()
    expect(page.locator("#commandPreview")).to_be_visible()
    page.locator("[data-copy-target='commandPreview']").click()
    expect(page.locator("#toast")).to_contain_text("Copied")

    assert not page.console_errors  # type: ignore[attr-defined]


def test_clear_target_url_button_clears_input_and_previews(page: Page) -> None:
    page.locator("#targetUrl").fill("https://www.nike.com/")
    page.locator("#developerDetails summary").click()
    expect(page.locator("#commandPreview")).to_contain_text("https://www.nike.com/")

    page.locator("#clearStartUrl").click()

    expect(page.locator("#targetUrl")).to_have_value("")
    expect(page.locator("#commandPreview")).not_to_contain_text("https://www.nike.com/")
    assert not page.console_errors  # type: ignore[attr-defined]


def test_browse_uses_native_folder_picker_endpoint_without_upload_control(page: Page) -> None:
    page.route(
        "**/workdir/pick-native",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "path": "/Users/test/Scout Runs/Estee",
                    "picked": True,
                    "cancelled": False,
                    "reason": "",
                }
            ),
        ),
    )

    page.locator("#pickDir").click()

    expect(page.locator("#workdir")).to_have_value("/Users/test/Scout Runs/Estee")
    expect(page.locator("#toast")).to_contain_text("Working directory selected")
    expect(page.locator("#nativeDirPicker")).to_have_count(0)
    expect(page.locator("#workdirDialog")).to_have_count(0)


def test_browse_cancel_does_not_open_secondary_dialog(page: Page) -> None:
    page.route(
        "**/workdir/pick-native",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {"path": "", "picked": False, "cancelled": True, "reason": "cancelled"}
            ),
        ),
    )

    page.locator("#pickDir").click()

    expect(page.locator("#toast")).to_contain_text("Folder selection cancelled")
    expect(page.locator("#nativeDirPicker")).to_have_count(0)
    expect(page.locator("#workdirDialog")).to_have_count(0)


def test_non_run_navigation_controls_are_intentionally_disabled(page: Page) -> None:
    screen_expectations = {
        "history": "Run History",
        "presets": "Presets",
        "targets": "Target Catalog",
        "data": "Data Browser",
        "integrations": "Integrations",
        "settings": "Settings",
        "help": "How to Use Scout",
    }
    for section, title in screen_expectations.items():
        control = page.locator(f"[data-rail-section='{section}']")
        expect(control).to_be_enabled()
        control.click()
        expect(page.locator("#screenTitle")).to_contain_text(title)
        expect(page.locator("#utilityScreen")).to_be_visible()

    for section, title in {"projects": "Projects", "settings": "Settings"}.items():
        control = page.locator(f"[data-top-section='{section}']")
        expect(control).to_be_enabled()
        control.click()
        expect(page.locator("#screenTitle")).to_contain_text(title)

    expect(page.locator("[data-top-section='docs']")).to_have_attribute("href", "/docs")


def test_each_use_case_changes_form_contract_and_payload(page: Page) -> None:
    expectations = {
        "products": "Product/category URL",
        "prism": "Company name, domain, or PRISM target URL",
        "company": "Company name, domain, or about URL",
        "investor": "Investor relations URL or company domain",
        "careers": "Careers URL or company domain",
        "jobs": "Company domain or job URL",
        "news": "Newsroom, blog URL, or company domain",
        "research": "URL, domain, or research prompt",
        "docs": "Documentation URL or sitemap URL",
        "website-quality": "Website URL",
    }
    for use_case, target_label in expectations.items():
        page.locator("#useCase").select_option(use_case)
        expect(page.locator("#targetLabel")).to_contain_text(target_label)
        expect(page.locator("#useCaseHelp")).not_to_be_empty()
        expect(page.locator("#expectedOutputs")).not_to_be_empty()
        page.locator("#developerDetails summary").click()
        expect(page.locator("#commandPreview")).to_contain_text(f"scout run {use_case}")
        if page.locator("#developerDetails").evaluate("node => node.open"):
            page.locator("#developerDetails summary").click()


def test_result_tabs_all_switch_visible_panels(page: Page) -> None:
    page.route(
        "**/app/runs",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "run_id": "app_run_tabs",
                    "status": "complete",
                    "use_case": "company",
                    "mode": "auto",
                    "target_url": "https://www.algolia.com/",
                    "events": [
                        {"stage": "complete", "message": "Run completed", "level": "success"}
                    ],
                    "records": [
                        {
                            "objectID": "company_algolia",
                            "name": "Algolia",
                            "url": "https://www.algolia.com/",
                            "citations": [{"field": "name"}],
                        }
                    ],
                    "sources": [
                        {
                            "source_url": "https://www.algolia.com/",
                            "provider": "crawl4ai",
                            "status": "ok",
                            "confidence": 1,
                        }
                    ],
                    "blocked_pages": [],
                    "artifacts": {
                        "records_json": "/tmp/records.json",
                        "report_md": "/tmp/report.md",
                    },
                    "browser_evidence": {
                        "url": "https://www.algolia.com/",
                        "title": "Algolia",
                        "note": "Evidence captured",
                    },
                }
            ),
        ),
    )
    page.locator("#useCase").select_option("company")
    page.locator("#targetUrl").fill("https://www.algolia.com/")
    page.locator("#startExecution").click()
    expect(page.locator("#resultsPanel")).to_be_visible()

    for panel in [
        "overviewPanel",
        "browserPanel",
        "recordsPanel",
        "sourcesPanel",
        "blockedPanel",
        "artifactsPanel",
        "logsPanel",
    ]:
        page.locator(f"[data-panel='{panel}']").click()
        expect(page.locator(f"#{panel}")).to_be_visible()


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


def _classify_control(control: dict[str, object]) -> str:
    if control.get("disabled"):
        return "intentionally_disabled"
    selector = str(control.get("selector", ""))
    tag = str(control.get("tag", ""))
    control_type = str(control.get("type", ""))
    href = str(control.get("href", ""))

    functional_selectors = {
        "#useCase",
        "#targetUrl",
        "#workdir",
        "#pickDir",
        "#startExecution",
        "#clearRun",
        "#cancelRun",
        "#clearStartUrl",
        "#addOption",
        "#developerDetails summary",
    }
    functional_prefixes = (
        "[data-mode=",
        "[data-remove-option=",
        "[data-add-option=",
        "[data-top-section=",
        "[data-rail-section=",
        "[data-panel=",
        "[data-copy-target=",
    )
    if selector in functional_selectors or selector.startswith(functional_prefixes):
        return "functional"
    if tag == "a" and href:
        return "functional"
    if tag == "input" and control_type in {"text", "password", "number", "url", ""}:
        return "functional"
    return "fail"
