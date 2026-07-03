from __future__ import annotations

import json
import runpy
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
        "POST /v1/hosted/map",
        "POST /v1/hosted/screenshot",
    ]
    assert "POST /v1/hosted/products" in payload["endpoints"]
    assert "POST /v1/hosted/run/company" in payload["endpoints"]
    assert "POST /v1/hosted/run/prism" in payload["endpoints"]
    assert "POST /v1/hosted/run/website-quality" in payload["endpoints"]
    assert payload["targets"]["scrape_crawl_map"] == "https://www.wikimedia.org/"
    assert payload["targets"]["screenshot"] == "https://www.cnn.com/"
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


def test_hosted_load_test_uses_tls_context_for_https_requests(monkeypatch) -> None:
    module = runpy.run_path(str(SCRIPT))
    planned = module["PlannedRequest"]("GET", "/v1/hosted/me")
    captured = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _size):
            return b"{}"

    def fake_urlopen(_req, timeout, context=None):
        captured["timeout"] = timeout
        captured["context"] = context
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    result = module["perform_request"](
        base_url="https://scout.example",
        key="test-key",
        planned=planned,
        timeout=11,
        user_index=1,
    )

    assert result["ok"] is True
    assert captured["timeout"] == 11
    assert captured["context"] is not None


def test_hosted_load_test_can_classify_expected_playground_throttles() -> None:
    module = runpy.run_path(str(SCRIPT))

    playground_throttle = {
        "endpoint": "POST /v1/playground/run",
        "status": 429,
        "ok": False,
        "latency_ms": 100,
        "error": "HTTP Error 429: Too Many Requests",
    }
    hosted_throttle = {
        "endpoint": "POST /v1/hosted/scrape",
        "status": 429,
        "ok": False,
        "latency_ms": 100,
        "error": "HTTP Error 429: Too Many Requests",
    }

    assert module["is_acceptable_result"](
        playground_throttle,
        allow_playground_throttle=True,
    )
    assert not module["is_acceptable_result"](
        hosted_throttle,
        allow_playground_throttle=True,
    )
    assert not module["is_acceptable_result"](
        playground_throttle,
        allow_playground_throttle=False,
    )
