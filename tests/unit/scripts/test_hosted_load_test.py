from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "scout-hosted-load-test"


def test_hosted_load_test_dry_run_covers_250_user_hosted_surface() -> None:
    result = subprocess.run(
        [str(SCRIPT), "--base-url", "https://scout.example", "--api-key", "test", "--dry-run"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)

    assert payload["users"] == 250
    assert payload["requests_per_user"] >= 15
    assert payload["total_planned_requests"] >= 3750
    assert payload["endpoints"][:5] == [
        "GET /v1/hosted/me",
        "POST /v1/hosted/scrape",
        "POST /v1/hosted/crawl",
        "POST /v1/hosted/products",
        "POST /v1/hosted/run/company",
    ]
    assert "POST /v1/hosted/run/prism" in payload["endpoints"]
    assert "POST /v1/hosted/run/website-quality" in payload["endpoints"]
    assert payload["targets"]["scrape_crawl_map"] == "https://www.wikimedia.org/"
    assert payload["targets"]["products"] == "https://www.lacoste.com/us/"
    assert payload["targets"]["intelligence"] == "https://www.microsoft.com/"
    assert payload["llm_expected"] == "disabled"


def test_hosted_load_test_can_include_all_playground_workflows() -> None:
    result = subprocess.run(
        [
            str(SCRIPT),
            "--base-url",
            "https://scout.example",
            "--api-key",
            "test",
            "--include-playground",
            "--dry-run",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)

    assert payload["requests_per_user"] >= 31
    assert payload["total_planned_requests"] >= 7750
    assert set(payload["playground_endpoints"]) == {
        "scrape",
        "crawl",
        "map",
        "screenshot",
        "products",
        "company",
        "prism",
        "investor",
        "careers",
        "jobs",
        "news",
        "research",
        "docs",
        "social",
        "locations",
        "website-quality",
    }


def test_hosted_load_test_requires_key_or_key_file_for_live_run() -> None:
    result = subprocess.run(
        [str(SCRIPT), "--base-url", "https://scout.example", "--users", "1"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "--api-key or --api-key-file is required" in result.stderr
