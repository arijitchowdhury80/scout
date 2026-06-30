"""Live certification for every Scout playground workflow.

Run with:
    SCOUT_LIVE_TESTS=1 python3 -m pytest tests/live/test_playground_live_workflows.py -v
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest


pytestmark = pytest.mark.live

PLAYGROUND_LIVE_CASES: list[dict[str, Any]] = [
    {
        "workflow": "scrape",
        "url": "https://example.com",
        "query": "Extract markdown from Example Domain",
        "min_records": 1,
    },
    {
        "workflow": "crawl",
        "url": "https://example.com",
        "query": "Crawl one level",
        "min_records": 1,
    },
    {
        "workflow": "map",
        "url": "https://example.com",
        "query": "Map public URLs",
        "min_records": 1,
    },
    {
        "workflow": "screenshot",
        "url": "https://example.com",
        "query": "Capture rendered evidence",
        "min_records": 1,
    },
    {
        "workflow": "extract",
        "url": "https://example.com",
        "query": "Extract structured page data",
        "min_records": 1,
    },
    {
        "workflow": "products",
        "url": "https://books.toscrape.com/",
        "query": "Extract book products",
        "min_records": 5,
    },
    {
        "workflow": "company",
        "url": "https://www.algolia.com",
        "query": "Algolia company overview",
        "min_records": 1,
    },
    {
        "workflow": "prism",
        "url": "https://www.algolia.com",
        "query": "Algolia PRISM bundle",
        "min_records": 1,
    },
    {
        "workflow": "investor",
        "url": "https://www.adobe.com/investor-relations.html",
        "query": "Adobe investor assets",
        "min_records": 1,
    },
    {
        "workflow": "careers",
        "url": "https://www.adobe.com/careers.html",
        "query": "Adobe careers and hiring",
        "min_records": 1,
    },
    {
        "workflow": "jobs",
        "url": "https://jobs.ashbyhq.com/kong",
        "query": "",
        "min_records": 1,
    },
    {
        "workflow": "news",
        "url": "https://www.algolia.com/blog",
        "query": "Latest Algolia blogs",
        "min_records": 1,
    },
    {
        "workflow": "research",
        "url": "https://openai.com/news",
        "query": "OpenAI news research summary",
        "min_records": 1,
    },
    {
        "workflow": "docs",
        "url": "https://www.algolia.com/doc/",
        "query": "Algolia documentation records",
        "min_records": 1,
    },
    {
        "workflow": "social",
        "url": "https://www.algolia.com",
        "query": "Algolia social profiles",
        "min_records": 1,
    },
    {
        "workflow": "locations",
        "url": "https://example.com",
        "query": "Location signals",
        "min_records": 1,
    },
    {
        "workflow": "website-quality",
        "url": "https://example.com",
        "query": "Website quality findings",
        "min_records": 1,
    },
]


@pytest.fixture(scope="module")
def scout_playground_server() -> Iterator[str]:
    if os.getenv("SCOUT_LIVE_TESTS") != "1":
        pytest.skip("Set SCOUT_LIVE_TESTS=1 to run live playground certification")

    port = _free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "scout.api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=Path(__file__).parents[2],
        env={
            **os.environ,
            "SCOUT_WORKDIR": "/tmp/scout-playground-live-cert",
            "SCOUT_PUBLIC_HOSTED_ONLY": "false",
        },
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
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


def test_all_playground_workflows_return_real_outputs(
    scout_playground_server: str, tmp_path: Path
) -> None:
    results = []
    for index, case in enumerate(PLAYGROUND_LIVE_CASES, start=1):
        result = _run_playground_case(scout_playground_server, case, index)
        results.append(result)
        assert result["http_status"] == 200, result
        assert result["success"] is True, result
        assert result["record_count"] >= case["min_records"], result
        assert result["json_download_len"] > 40, result
        assert result["markdown_download_len"] > 40, result
        assert result["blocked_count"] >= 0, result

    report_path = tmp_path / "playground-live-results.json"
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")


def _run_playground_case(base_url: str, case: dict[str, Any], index: int) -> dict[str, Any]:
    payload = {
        "workflow": case["workflow"],
        "url": case["url"],
        "query": case["query"],
        "output_format": "json",
        "max_items": 10,
    }
    data = json.dumps(payload).encode()
    request = urllib.request.Request(
        f"{base_url}/v1/playground/run",
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Forwarded-For": f"198.51.100.{index}",
        },
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read().decode())
        return {
            "workflow": case["workflow"],
            "http_status": exc.code,
            "success": False,
            "record_count": 0,
            "blocked_count": 0,
            "json_download_len": 0,
            "markdown_download_len": 0,
            "error": body,
            "duration_s": round(time.time() - started, 2),
        }

    return {
        "workflow": case["workflow"],
        "url": case["url"],
        "http_status": 200,
        "success": bool(body.get("success")),
        "record_count": int(body.get("summary", {}).get("record_count") or 0),
        "blocked_count": int(body.get("summary", {}).get("blocked_count") or 0),
        "json_download_len": len(body.get("downloads", {}).get("json", "")),
        "markdown_download_len": len(body.get("downloads", {}).get("markdown", "")),
        "error": body.get("error", ""),
        "duration_s": round(time.time() - started, 2),
    }


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_health(base_url: str) -> None:
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("Timed out waiting for Scout playground test server")
