"""Scout launch-readiness e2e test harness.

Runs the test matrix in docs/test-results-2026-07-26/00-test-matrix.md against
either:

  - LIVE PROD authed hosted API (https://scout.chowmes.com/v1/hosted/*), using
    SCOUT_BASE_URL + SCOUT_API_KEY from the environment, or
  - the public, no-auth demo endpoints (/v1/demo/*) via --dry-run, which needs
    no API key and exists to prove this harness works end to end.

Design constraints (see docs/test-results-2026-07-26/00-test-matrix.md):
  - Never hardcode a key. SCOUT_BASE_URL and SCOUT_API_KEY come from the
    environment only.
  - Async-first: hosted POSTs return 202 + job_url; poll GET /v1/hosted/jobs/
    {job_id} until status is a terminal state, then read `result`.
  - Every raw response is saved to
    docs/test-results-2026-07-26/<site>/<capability>.json (or
    _dry-run/<capability>.json for --dry-run), and a verdict row (pass/fail/na
    + evidence path) is appended to docs/test-results-2026-07-26/verdicts.csv.
  - /extract, /harvest, /app/* are marked `na` unconditionally — never called
    against prod.

Usage:
    python3 scout_e2e.py --dry-run
    SCOUT_BASE_URL=https://scout.chowmes.com SCOUT_API_KEY=... python3 scout_e2e.py
"""

from __future__ import annotations

import argparse
import base64
import csv
import dataclasses
import json
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

RESULTS_DIR = Path(__file__).resolve().parent
DEFAULT_BASE_URL = "https://scout.chowmes.com"

SITES = [
    "algolia.com",
    "adobe.com",
    "salesforce.com",
    "lacoste.com",
    "eyebuydirect.com",
]

VERTICAL_SITES = ["algolia.com", "adobe.com", "salesforce.com"]
PRODUCT_SITES = ["lacoste.com", "eyebuydirect.com"]
PRISM_SITE = "algolia.com"

# Terminal job states we accept as "done"; anything else keeps polling.
DONE_STATES = {"done", "complete", "completed", "succeeded", "success"}
ERROR_STATES = {"error", "failed", "failure"}

TERMINATE_AFTER_SECONDS = 600
POLL_INTERVAL_SECONDS = 8


@dataclasses.dataclass
class Verdict:
    site: str
    capability: str
    verdict: str  # pass | fail | na
    http_codes: str
    evidence_path: str
    notes: str = ""


class ScoutHarness:
    """Thin httpx-based client that runs one matrix row at a time."""

    def __init__(self, base_url: str, api_key: str | None, out_root: Path) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.out_root = out_root
        self.verdicts: list[Verdict] = []
        self._client = httpx.Client(timeout=60.0)

    def close(self) -> None:
        self._client.close()

    # --- low-level helpers -------------------------------------------------

    def _auth_headers(self) -> dict[str, str]:
        if not self.api_key:
            raise RuntimeError("No API key configured; cannot call authed hosted endpoints.")
        return {"Authorization": f"Bearer {self.api_key}"}

    def _retry_on_429(self, do_request: Callable[[], httpx.Response]) -> httpx.Response:
        """Retry on HTTP 429, respecting Retry-After if present.

        The hosted rate limit is 60 req/60s (scout/api/config.py
        hosted_rate_limit_max_requests). Without backoff here, one 429 during
        job polling cascades into every subsequent call 429-ing too, since we
        keep firing requests inside the same blocked window.
        """
        max_attempts = 6
        for attempt in range(max_attempts):
            resp = do_request()
            if resp.status_code != 429:
                return resp
            retry_after = resp.headers.get("Retry-After")
            try:
                wait_s = float(retry_after) if retry_after else 65.0
            except ValueError:
                wait_s = 65.0
            print(
                f"  [429] rate-limited, sleeping {wait_s:.0f}s before retry "
                f"({attempt + 1}/{max_attempts})"
            )
            time.sleep(wait_s)
        return resp  # give up after max_attempts; caller will raise_for_status()

    def _post(self, path: str, body: dict[str, Any], authed: bool) -> httpx.Response:
        headers = self._auth_headers() if authed else {}
        return self._retry_on_429(
            lambda: self._client.post(f"{self.base_url}{path}", json=body, headers=headers)
        )

    def _get(self, path: str, authed: bool) -> httpx.Response:
        headers = self._auth_headers() if authed else {}
        return self._retry_on_429(
            lambda: self._client.get(f"{self.base_url}{path}", headers=headers)
        )

    def _save_json(self, site: str, capability: str, payload: Any) -> Path:
        site_dir = self.out_root / site
        site_dir.mkdir(parents=True, exist_ok=True)
        out_path = site_dir / f"{capability}.json"
        out_path.write_text(json.dumps(payload, indent=2, default=str))
        return out_path

    def _save_screenshot(self, site: str, capability: str, b64_png: str) -> Path | None:
        if not b64_png:
            return None
        site_dir = self.out_root / site
        site_dir.mkdir(parents=True, exist_ok=True)
        out_path = site_dir / f"{capability}.png"
        try:
            raw = base64.b64decode(b64_png)
        except Exception:
            return None
        out_path.write_bytes(raw)
        return out_path

    # --- async job flow (authed hosted endpoints) ---------------------------

    def _poll_job(self, job_id: str, http_codes: list[str]) -> dict[str, Any]:
        deadline = time.monotonic() + TERMINATE_AFTER_SECONDS
        while time.monotonic() < deadline:
            resp = self._get(f"/v1/hosted/jobs/{job_id}", authed=True)
            http_codes.append(str(resp.status_code))
            resp.raise_for_status()
            data = resp.json()
            status = str(data.get("status", "")).lower()
            if status in DONE_STATES or status in ERROR_STATES:
                return data
            time.sleep(POLL_INTERVAL_SECONDS)
        raise TimeoutError(
            f"Job {job_id} did not reach a terminal state within {TERMINATE_AFTER_SECONDS}s"
        )

    def run_authed_job(
        self,
        site: str,
        capability: str,
        path: str,
        body: dict[str, Any],
        result_ok: Callable[[dict[str, Any]], tuple[bool, str]],
    ) -> None:
        """POST an authed hosted job, poll to completion, save + verdict."""
        http_codes: list[str] = []
        try:
            resp = self._post(path, body, authed=True)
            http_codes.append(str(resp.status_code))
            resp.raise_for_status()
            enqueue_payload = resp.json()

            if resp.status_code == 202 and "job_id" in enqueue_payload:
                job_data = self._poll_job(enqueue_payload["job_id"], http_codes)
            else:
                # Synchronous fallback (HOSTED_ASYNC_FIRST=false or admission
                # let it run inline).
                job_data = enqueue_payload

            evidence_path = self._save_json(site, capability, job_data)

            status = str(job_data.get("status", "")).lower()
            if status in ERROR_STATES:
                self._record(
                    site,
                    capability,
                    "fail",
                    http_codes,
                    evidence_path,
                    job_data.get("error", "job errored"),
                )
                return

            result = job_data.get("result") if "result" in job_data else job_data
            ok, note = result_ok(result or {})
            if capability == "screenshot":
                shot = (result or {}).get("screenshot", result or {})
                self._save_screenshot(site, capability, shot.get("screenshot_base64", ""))
            self._record(
                site, capability, "pass" if ok else "fail", http_codes, evidence_path, note
            )
        except Exception as exc:  # noqa: BLE001 - harness must never crash the matrix run
            evidence_path = self._save_json(site, capability, {"error": str(exc)})
            self._record(site, capability, "fail", http_codes, evidence_path, f"exception: {exc}")

    # --- public demo flow (dry-run) -----------------------------------------

    def run_demo(
        self,
        capability: str,
        path: str,
        body: dict[str, Any],
        result_ok: Callable[[dict[str, Any]], tuple[bool, str]],
    ) -> None:
        http_codes: list[str] = []
        site = "_dry-run"
        try:
            resp = self._post(path, body, authed=False)
            http_codes.append(str(resp.status_code))
            resp.raise_for_status()
            payload = resp.json()
            evidence_path = self._save_json(site, capability, payload)
            ok, note = result_ok(payload)
            self._record(
                site, capability, "pass" if ok else "fail", http_codes, evidence_path, note
            )
        except Exception as exc:  # noqa: BLE001
            evidence_path = self._save_json(site, capability, {"error": str(exc)})
            self._record(site, capability, "fail", http_codes, evidence_path, f"exception: {exc}")

    def record_na(self, site: str, capability: str, notes: str) -> None:
        self._record(site, capability, "na", [], Path(""), notes)

    def _record(
        self,
        site: str,
        capability: str,
        verdict: str,
        http_codes: list[str],
        evidence_path: Path,
        notes: str,
    ) -> None:
        self.verdicts.append(
            Verdict(
                site=site,
                capability=capability,
                verdict=verdict,
                http_codes=",".join(http_codes),
                evidence_path=str(evidence_path),
                notes=notes,
            )
        )
        print(
            f"[{verdict.upper():4}] {site:20} {capability:12} http={','.join(http_codes) or '-'} {notes}"
        )

    def write_verdicts_csv(self, filename: str = "verdicts.csv") -> Path:
        out_path = self.out_root / filename
        with out_path.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                ["site", "capability", "verdict", "http_codes", "evidence_path", "notes"]
            )
            for v in self.verdicts:
                writer.writerow(
                    [v.site, v.capability, v.verdict, v.http_codes, v.evidence_path, v.notes]
                )
        return out_path


# --- result validators (one per capability) ---------------------------------


def _ok_scrape(result: dict[str, Any]) -> tuple[bool, str]:
    scrape = result.get("scrape", result)
    success = bool(scrape.get("success"))
    word_count = int(scrape.get("metadata", {}).get("word_count", 0) or 0)
    if success and word_count > 0:
        return True, f"word_count={word_count}"
    return False, f"success={success} word_count={word_count}"


def _ok_crawl(result: dict[str, Any], min_pages: int = 10) -> tuple[bool, str]:
    crawl = result.get("crawl", result)
    total = int(crawl.get("total_pages", 0) or 0)
    pages = crawl.get("pages", [])
    any_page_ok = any(p.get("success") and p.get("markdown") for p in pages) if pages else False
    if total >= min_pages and (any_page_ok or not pages):
        return True, f"total_pages={total}"
    return False, f"total_pages={total} (need >={min_pages}) any_page_ok={any_page_ok}"


def _ok_map(result: dict[str, Any]) -> tuple[bool, str]:
    map_result = result.get("map", result)
    total = int(map_result.get("total", 0) or 0)
    urls = map_result.get("urls", [])
    if total >= 1 and len(urls) >= 1:
        return True, f"total={total}"
    return False, f"total={total} urls={len(urls)}"


def _ok_screenshot(result: dict[str, Any]) -> tuple[bool, str]:
    shot = result.get("screenshot", result)
    b64 = shot.get("screenshot_base64", "")
    width = int(shot.get("width", 0) or 0)
    height = int(shot.get("height", 0) or 0)
    if not b64:
        return False, "empty screenshot_base64"
    try:
        is_png = base64.b64decode(b64)[:8] == b"\x89PNG\r\n\x1a\n"
    except Exception:
        is_png = False
    if is_png and width > 0 and height > 0:
        return True, f"{width}x{height}"
    return False, f"is_png={is_png} width={width} height={height}"


def _ok_run(result: dict[str, Any], min_records: int = 1) -> tuple[bool, str]:
    run = result.get("run", result)
    success = bool(run.get("success"))
    total = int(run.get("total_records", 0) or 0)
    if success and total >= min_records:
        return True, f"total_records={total}"
    return False, f"success={success} total_records={total} (need >={min_records})"


def _ok_products(result: dict[str, Any], min_records: int = 100) -> tuple[bool, str]:
    products = result.get("products", result)
    total = int(products.get("total_products", 0) or 0)
    if total >= min_records:
        return True, f"total_products={total}"
    return False, f"total_products={total} (need >={min_records})"


# --- demo (dry-run) validators ------------------------------------------------


def _ok_demo_preview(result: dict[str, Any]) -> tuple[bool, str]:
    success = bool(result.get("success"))
    record = result.get("record", {})
    if success and record:
        return True, "preview non-empty"
    return False, f"success={success} record_empty={not record}"


# --- matrix runners ------------------------------------------------------------


def run_dry_run(harness: ScoutHarness) -> None:
    """Hit only the public /v1/demo/* endpoints. No API key required."""
    harness.run_demo("scrape", "/v1/demo/scrape", {"url": "https://example.com"}, _ok_demo_preview)
    harness.run_demo("map", "/v1/demo/map", {"url": "https://example.com"}, _ok_demo_preview)
    harness.run_demo("crawl", "/v1/demo/crawl", {"url": "https://example.com"}, _ok_demo_preview)
    harness.run_demo(
        "products", "/v1/demo/products", {"url": "https://example.com"}, _ok_demo_preview
    )


def run_authed_matrix(harness: ScoutHarness) -> None:
    """Run the full authed launch-readiness matrix against LIVE PROD."""
    for site in SITES:
        url = f"https://{site}"

        harness.run_authed_job(site, "scrape", "/v1/hosted/scrape", {"url": url}, _ok_scrape)
        harness.run_authed_job(
            site,
            "crawl",
            "/v1/hosted/crawl",
            {"url": url, "max_pages": 25},
            lambda r: _ok_crawl(r, 10),
        )
        harness.run_authed_job(
            site, "map", "/v1/hosted/map", {"url": url, "max_pages": 100}, _ok_map
        )
        harness.run_authed_job(
            site,
            "screenshot",
            "/v1/hosted/screenshot",
            {"url": url, "full_page": True},
            _ok_screenshot,
        )

    for site in VERTICAL_SITES:
        url = f"https://{site}"
        harness.run_authed_job(
            site,
            "company",
            "/v1/hosted/run/company",
            {"use_case": "company", "url": url, "max_records": 50},
            lambda r: _ok_run(r, 1),
        )
        harness.run_authed_job(
            site,
            "careers",
            "/v1/hosted/run/careers",
            {"use_case": "careers", "url": url, "max_records": 50},
            lambda r: _ok_run(r, 1),
        )

    for site in PRODUCT_SITES:
        url = f"https://{site}"
        harness.run_authed_job(
            site,
            "products",
            "/v1/hosted/products",
            {"start_url": url, "max_products": 100, "max_categories": 5},
            lambda r: _ok_products(r, 100),
        )

    harness.run_authed_job(
        PRISM_SITE,
        "prism",
        "/v1/hosted/run/prism",
        {"use_case": "prism", "url": f"https://{PRISM_SITE}", "max_records": 100},
        lambda r: _ok_run(r, 1),
    )

    na_reason = "N/A on hosted per matrix scope — never call against prod (see 00-test-matrix.md)"
    for site in SITES:
        harness.record_na(site, "extract", na_reason)
        harness.record_na(site, "harvest", na_reason)
        harness.record_na(site, "app", na_reason)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Hit only the public /v1/demo/* endpoints (no API key needed).",
    )
    parser.add_argument(
        "--out",
        default=str(RESULTS_DIR),
        help="Root output directory for evidence + verdicts.csv (default: docs/test-results-2026-07-26/)",
    )
    args = parser.parse_args()

    base_url = os.environ.get("SCOUT_BASE_URL", DEFAULT_BASE_URL)
    api_key = os.environ.get("SCOUT_API_KEY")
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    if not args.dry_run and not api_key:
        print(
            "ERROR: SCOUT_API_KEY is not set. Run with --dry-run to exercise the "
            "public demo endpoints, or set SCOUT_API_KEY (and optionally "
            "SCOUT_BASE_URL) to run the authed matrix.",
            file=sys.stderr,
        )
        return 2

    harness = ScoutHarness(base_url=base_url, api_key=api_key, out_root=out_root)
    try:
        if args.dry_run:
            print(f"Running DRY-RUN (public /v1/demo/*) against {base_url}")
            run_dry_run(harness)
        else:
            print(f"Running AUTHED MATRIX against {base_url}")
            run_authed_matrix(harness)
        verdicts_path = harness.write_verdicts_csv()
        print(f"\nVerdicts written to {verdicts_path}")

        failures = [v for v in harness.verdicts if v.verdict == "fail"]
        print(
            f"\n{len(harness.verdicts)} rows: "
            f"{sum(1 for v in harness.verdicts if v.verdict == 'pass')} pass, "
            f"{len(failures)} fail, "
            f"{sum(1 for v in harness.verdicts if v.verdict == 'na')} na"
        )
        return 1 if failures else 0
    finally:
        harness.close()


if __name__ == "__main__":
    raise SystemExit(main())
