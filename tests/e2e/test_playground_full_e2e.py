"""Full browser-level certification for the public Scout playground."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Page, Route, sync_playwright


_REPO_ROOT = Path(__file__).resolve().parents[2]
_WEBSITE_DIR = _REPO_ROOT / "website"


PLAYGROUND_CASES: list[dict[str, Any]] = [
    {
        "workflow": "scrape",
        "url": "example.com",
        "normalized_url": "https://example.com",
        "query": "Extract markdown from Example Domain",
        "help": "clean markdown",
        "max_items": 1,
    },
    {
        "workflow": "crawl",
        "url": "https://example.com",
        "normalized_url": "https://example.com",
        "query": "Crawl one level",
        "help": "five pages",
        "max_items": 5,
    },
    {
        "workflow": "map",
        "url": "www.algolia.com",
        "normalized_url": "https://www.algolia.com",
        "query": "Find public URLs",
        "help": "Discover public site URLs",
        "max_items": 5,
    },
    {
        "workflow": "screenshot",
        "url": "https://www.nike.com",
        "normalized_url": "https://www.nike.com",
        "query": "Capture rendered evidence",
        "help": "screenshot",
        "max_items": 1,
    },
    {
        "workflow": "products",
        "url": "www.nike.com/w/mens-shoes",
        "normalized_url": "https://www.nike.com/w/mens-shoes",
        "query": "Extract ten product records",
        "help": "product records",
        "max_items": 10,
    },
    {
        "workflow": "company",
        "url": "www.algolia.com",
        "normalized_url": "https://www.algolia.com",
        "query": "Company overview",
        "help": "company overview",
        "max_items": 10,
    },
    {
        "workflow": "prism",
        "url": "www.constructor.io",
        "normalized_url": "https://www.constructor.io",
        "query": "PRISM prospect bundle",
        "help": "prospect research",
        "max_items": 10,
    },
    {
        "workflow": "investor",
        "url": "www.adobe.com/investor-relations.html",
        "normalized_url": "https://www.adobe.com/investor-relations.html",
        "query": "Investor reports",
        "help": "Investor",
        "max_items": 10,
    },
    {
        "workflow": "careers",
        "url": "www.adobe.com/careers.html",
        "normalized_url": "https://www.adobe.com/careers.html",
        "query": "Careers and hiring",
        "help": "career pages",
        "max_items": 10,
    },
    {
        "workflow": "jobs",
        "url": "jobs.ashbyhq.com/kong",
        "normalized_url": "https://jobs.ashbyhq.com/kong",
        "query": "Director customer success jobs",
        "help": "job records",
        "max_items": 10,
    },
    {
        "workflow": "news",
        "url": "www.algolia.com/blog",
        "normalized_url": "https://www.algolia.com/blog",
        "query": "Latest blogs",
        "help": "newsroom",
        "max_items": 10,
    },
    {
        "workflow": "social",
        "url": "www.nike.com",
        "normalized_url": "https://www.nike.com",
        "query": "Social profiles",
        "help": "social profile",
        "max_items": 10,
    },
    {
        "workflow": "locations",
        "url": "www.homedepot.com",
        "normalized_url": "https://www.homedepot.com",
        "query": "Store locations",
        "help": "location page",
        "max_items": 10,
    },
    {
        "workflow": "website-quality",
        "url": "www.britishairways.com",
        "normalized_url": "https://www.britishairways.com",
        "query": "Website quality review",
        "help": "quality findings",
        "max_items": 10,
    },
    {
        "workflow": "extract",
        "url": "https://example.com",
        "normalized_url": "https://example.com",
        "query": "Extract structured facts",
        "help": "structured record",
        "max_items": 1,
    },
    {
        "workflow": "research",
        "url": "openai.com/news",
        "normalized_url": "https://openai.com/news",
        "query": "Research summary",
        "help": "research records",
        "max_items": 10,
    },
    {
        "workflow": "docs",
        "url": "www.algolia.com/doc/",
        "normalized_url": "https://www.algolia.com/doc/",
        "query": "Documentation records",
        "help": "docs pages",
        "max_items": 10,
    },
]


@pytest.fixture(scope="module")
def static_site_url() -> Generator[str]:
    """Serve the static website so browser JS can run exactly as shipped."""
    port = _free_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "http.server",
            str(port),
            "--bind",
            "127.0.0.1",
            "--directory",
            str(_WEBSITE_DIR),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_for_static_site(base_url)
        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def test_playground_all_workflows_are_functional_from_ui(
    static_site_url: str, tmp_path: Path
) -> None:
    """Exercise every visible playground workflow, tab, download, and generated payload."""
    observed_requests: list[dict[str, Any]] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(accept_downloads=True, viewport={"width": 1440, "height": 1000})
        console_errors: list[str] = []
        page.on(
            "console",
            lambda msg: (
                console_errors.append(f"{msg.type}: {msg.text}") if msg.type == "error" else None
            ),
        )
        page.route(
            "**/v1/playground/run", lambda route: _fulfill_playground(route, observed_requests)
        )

        page.goto(f"{static_site_url}/quickstart.html", wait_until="networkidle")
        assert page.locator("text=Scout Playground").count() >= 1

        workflow_values = page.locator("#playgroundWorkflow option").evaluate_all(
            "(options) => options.map((option) => option.value)"
        )
        assert workflow_values == [case["workflow"] for case in PLAYGROUND_CASES]

        for case in PLAYGROUND_CASES:
            _exercise_workflow(page, case, tmp_path)

        browser.close()

    assert not console_errors
    assert [request["workflow"] for request in observed_requests] == [
        case["workflow"] for case in PLAYGROUND_CASES
    ]
    for request, case in zip(observed_requests, PLAYGROUND_CASES, strict=True):
        assert request["url"] == case["normalized_url"]
        assert request["query"] == case["query"]
        assert request["max_items"] == case["max_items"]


def _exercise_workflow(page: Page, case: dict[str, Any], tmp_path: Path) -> None:
    workflow = case["workflow"]
    page.locator("#playgroundWorkflow").select_option(workflow)
    assert case["help"].lower() in page.locator("#playgroundCapabilityHelp").inner_text().lower()

    page.locator("#playgroundUrl").fill(case["url"])
    page.locator("#playgroundQuery").fill(case["query"])
    page.locator("#playgroundOutputFormat").select_option("json")

    curl = page.locator("#playgroundCurl").inner_text()
    assert f'"workflow":"{workflow}"' in curl
    assert f'"url":"{case["normalized_url"]}"' in curl
    assert "https://scout.chowmes.com/v1/playground/run" in curl

    page.locator('button[type="submit"]').click()
    page.wait_for_function(
        "document.querySelector('#playgroundStatus').textContent.includes('Complete:')",
        timeout=10_000,
    )
    assert "Please enter a URL" not in page.content()
    assert "Enter a public URL first" not in page.locator("#playgroundStatus").inner_text()

    page.locator('[data-playground-tab="preview"]').click()
    assert page.locator("#playgroundResults").is_visible()
    assert workflow in page.locator("#playgroundResults").inner_text().lower()

    page.locator('[data-playground-tab="json"]').click()
    assert page.locator("#playgroundJson").is_visible()
    json_text = page.locator("#playgroundJson").inner_text()
    assert f'"workflow": "{workflow}"' in json_text
    assert f"{workflow} demo record" in json_text

    page.locator('[data-playground-tab="markdown"]').click()
    assert page.locator("#playgroundMarkdown").is_visible()
    assert f"{workflow} demo record" in page.locator("#playgroundMarkdown").inner_text()

    page.locator('[data-playground-tab="curl"]').click()
    assert page.locator("#playgroundCurl").is_visible()
    assert f'"workflow":"{workflow}"' in page.locator("#playgroundCurl").inner_text()

    assert page.locator("#playgroundDownloadJson").is_enabled()
    assert page.locator("#playgroundDownloadMarkdown").is_enabled()

    with page.expect_download() as json_download_info:
        page.locator("#playgroundDownloadJson").click()
    json_download = json_download_info.value
    json_path = tmp_path / json_download.suggested_filename
    json_download.save_as(json_path)
    assert json.loads(json_path.read_text(encoding="utf-8"))["workflow"] == workflow

    with page.expect_download() as markdown_download_info:
        page.locator("#playgroundDownloadMarkdown").click()
    markdown_download = markdown_download_info.value
    markdown_path = tmp_path / markdown_download.suggested_filename
    markdown_download.save_as(markdown_path)
    assert f"{workflow} demo record" in markdown_path.read_text(encoding="utf-8")


def _fulfill_playground(route: Route, observed_requests: list[dict[str, Any]]) -> None:
    request_payload = json.loads(route.request.post_data or "{}")
    observed_requests.append(request_payload)
    workflow = request_payload["workflow"]
    record = {
        "objectID": f"{workflow}-demo-1",
        "record_type": f"{workflow}.playground",
        "title": f"{workflow} demo record",
        "url": request_payload["url"],
        "source_url": request_payload["url"],
        "citations": [
            {
                "source_url": request_payload["url"],
                "field": "title",
                "snippet": f"{workflow} demo record",
                "confidence": 0.9,
            }
        ],
    }
    download_json = {
        "workflow": workflow,
        "records": [record],
        "blocked_pages": [],
    }
    response_payload = {
        "success": True,
        "workflow": workflow,
        "url": request_payload["url"],
        "output_format": request_payload["output_format"],
        "limits": {"max_records": request_payload["max_items"], "timeout_ms": 30_000},
        "summary": {
            "record_count": 1,
            "blocked_count": 0,
            "duration_ms": 12,
            "capped": True,
        },
        "records": [record],
        "blocked_pages": [],
        "downloads": {
            "json": json.dumps(download_json, indent=2),
            "markdown": f"# {workflow} demo record\n\nSource: {request_payload['url']}\n",
        },
        "download_filenames": {
            "json": f"scout-playground-{workflow}.json",
            "markdown": f"scout-playground-{workflow}.md",
        },
        "error": "",
    }
    route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps(response_payload),
    )


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_static_site(base_url: str) -> None:
    import urllib.request

    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/quickstart.html", timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("Timed out waiting for static website server")
