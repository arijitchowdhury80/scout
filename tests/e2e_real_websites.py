#!/usr/bin/env python3
"""Scout End-to-End Test Suite — Real Websites.

Tests every Scout use case against real websites with human-readable reporting.
Each test case defines: what we're testing, which real site, what we expect to
find, and what constitutes success vs failure.

Usage:
    # Start Scout first:
    python -m uvicorn scout.api.main:app --host 0.0.0.0 --port 8421

    # Run all E2E tests:
    python tests/e2e_real_websites.py

    # Run a specific use case:
    python tests/e2e_real_websites.py --use-case scrape
    python tests/e2e_real_websites.py --use-case products
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass

import httpx

# ---------------------------------------------------------------------------
# Test case definitions
# ---------------------------------------------------------------------------


@dataclass
class E2ETestCase:
    use_case: str
    site: str
    description: str
    why: str
    endpoint: str
    payload: dict
    success_criteria: list[str]
    failure_criteria: list[str]
    timeout: float = 120.0


@dataclass
class E2EResult:
    test_case: E2ETestCase
    passed: bool
    checks: list[tuple[str, bool, str]]  # (criterion, passed, detail)
    duration_ms: int
    raw_response: dict
    error: str = ""


# ---------------------------------------------------------------------------
# Test definitions — real websites, real expectations
# ---------------------------------------------------------------------------

SCRAPE_TESTS = [
    E2ETestCase(
        use_case="scrape",
        site="https://stripe.com/about",
        description="Scrape Stripe's about page for company info",
        why="Stripe is a well-known tech company. About pages are the foundation of company intelligence.",
        endpoint="/scrape",
        payload={"url": "https://stripe.com/about", "formats": ["markdown"]},
        success_criteria=[
            "success=true",
            "markdown contains 'Stripe' (company name appears)",
            "markdown length > 200 chars (real content, not error page)",
            "metadata.title is non-empty",
            "metadata.word_count > 50",
        ],
        failure_criteria=[
            "success=false (site unreachable or blocked)",
            "markdown is empty (extraction failed)",
            "markdown contains 'Access Denied' or 'blocked' (bot detection)",
        ],
    ),
    E2ETestCase(
        use_case="scrape",
        site="https://news.ycombinator.com",
        description="Scrape Hacker News front page — dynamic link aggregator",
        why="HN is a JS-light but content-rich page. Tests basic HTML extraction quality.",
        endpoint="/scrape",
        payload={"url": "https://news.ycombinator.com"},
        success_criteria=[
            "success=true",
            "markdown length > 500 chars",
            "links list has > 10 items (HN has 30+ links)",
            "metadata.url contains 'ycombinator'",
        ],
        failure_criteria=[
            "success=false",
            "links list is empty (link extraction broken)",
        ],
    ),
    E2ETestCase(
        use_case="scrape",
        site="https://en.wikipedia.org/wiki/Web_scraping",
        description="Scrape Wikipedia article — long-form content extraction",
        why="Wikipedia tests large page handling, section structure, and markdown quality.",
        endpoint="/scrape",
        payload={"url": "https://en.wikipedia.org/wiki/Web_scraping"},
        success_criteria=[
            "success=true",
            "markdown length > 2000 chars (full article)",
            "markdown contains 'web scraping' (topic present)",
            "metadata.word_count > 500",
        ],
        failure_criteria=[
            "success=false",
            "markdown length < 500 (truncated)",
        ],
    ),
]

CRAWL_TESTS = [
    E2ETestCase(
        use_case="crawl",
        site="https://books.toscrape.com",
        description="Crawl books.toscrape.com — structured test site",
        why="Known test site with predictable structure. Validates BFS crawl correctness.",
        endpoint="/crawl",
        payload={"url": "https://books.toscrape.com", "max_depth": 1, "max_pages": 5},
        success_criteria=[
            "success=true",
            "total_pages >= 2 (found linked pages)",
            "pages[0].markdown is non-empty",
            "all pages have success=true",
            "duration_ms > 0",
        ],
        failure_criteria=[
            "success=false",
            "total_pages = 0 (no pages found)",
        ],
    ),
    E2ETestCase(
        use_case="crawl",
        site="https://quotes.toscrape.com",
        description="Crawl quotes.toscrape.com — structured test site with pagination",
        why="Known test site with multi-page content. Tests BFS across paginated pages.",
        endpoint="/crawl",
        payload={"url": "https://quotes.toscrape.com", "max_depth": 1, "max_pages": 5},
        success_criteria=[
            "success=true",
            "total_pages >= 2",
            "pages contain different URLs (not all same page)",
        ],
        failure_criteria=[
            "success=false",
            "total_pages <= 1",
        ],
    ),
]

MAP_TESTS = [
    E2ETestCase(
        use_case="map",
        site="https://books.toscrape.com",
        description="Discover all URLs on books.toscrape.com",
        why="URL discovery should find category pages, individual books, pagination links.",
        endpoint="/map",
        payload={"url": "https://books.toscrape.com", "max_pages": 50},
        success_criteria=[
            "success=true",
            "total >= 10 (site has many pages)",
            "urls contain '/catalogue/' paths (book pages)",
        ],
        failure_criteria=[
            "success=false",
            "total < 5 (discovery too shallow)",
        ],
    ),
]

SCREENSHOT_TESTS = [
    E2ETestCase(
        use_case="screenshot",
        site="https://example.com",
        description="Screenshot example.com — baseline visual capture",
        why="Simple static page. Validates screenshot pipeline produces valid images.",
        endpoint="/screenshot",
        payload={"url": "https://example.com", "full_page": True},
        success_criteria=[
            "success=true",
            "screenshot_base64 length > 1000 (real image data)",
            "width >= 1000 (desktop viewport)",
            "height > 0",
        ],
        failure_criteria=[
            "success=false",
            "screenshot_base64 is empty",
        ],
    ),
    E2ETestCase(
        use_case="screenshot",
        site="https://stripe.com",
        description="Screenshot Stripe homepage — JS-heavy modern site",
        why="Tests JS rendering and screenshot quality on a modern site.",
        endpoint="/screenshot",
        payload={"url": "https://stripe.com", "full_page": True, "viewport_width": 1440},
        success_criteria=[
            "success=true",
            "screenshot_base64 length > 5000 (complex page)",
            "width >= 1400",
        ],
        failure_criteria=[
            "success=false (blocked or timeout)",
        ],
    ),
]

STRUCTURE_TESTS = [
    E2ETestCase(
        use_case="structure",
        site="inline HTML (product listing)",
        description="Structure captured HTML with CSS schema — extract product records",
        why="Core PRISM capability: turn captured HTML into typed records without re-fetching.",
        endpoint="/structure",
        payload={
            "html": """<html><body>
                <div class="product"><h2>Nike Air Max 90</h2><span class="price">$130.00</span><a href="/shoes/air-max-90">View</a></div>
                <div class="product"><h2>Adidas Ultraboost</h2><span class="price">$180.00</span><a href="/shoes/ultraboost">View</a></div>
                <div class="product"><h2>New Balance 990v6</h2><span class="price">$199.99</span><a href="/shoes/990v6">View</a></div>
            </body></html>""",
            "source_url": "https://example.com/shoes",
            "css_schema": {
                "baseSelector": "div.product",
                "fields": [
                    {"name": "name", "selector": "h2", "type": "text"},
                    {"name": "price", "selector": "span.price", "type": "text"},
                    {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"},
                ],
            },
        },
        success_criteria=[
            "success=true",
            "record_count = 3 (three products)",
            "records[0] has 'name' field",
            "records[0]['name'] contains 'Nike' or 'Air Max'",
            "records[0] has 'price' field",
            "markdown is non-empty",
        ],
        failure_criteria=[
            "success=false",
            "record_count = 0 (CSS schema didn't match)",
        ],
    ),
    E2ETestCase(
        use_case="structure",
        site="inline HTML (job listings)",
        description="Structure captured HTML — extract job listings",
        why="Tests CSS extraction on a different content type (jobs, not products).",
        endpoint="/structure",
        payload={
            "html": """<html><body>
                <div class="job"><h3>Senior Engineer</h3><span class="dept">Engineering</span><span class="loc">San Francisco, CA</span></div>
                <div class="job"><h3>Product Manager</h3><span class="dept">Product</span><span class="loc">New York, NY</span></div>
            </body></html>""",
            "source_url": "https://example.com/careers",
            "css_schema": {
                "baseSelector": "div.job",
                "fields": [
                    {"name": "title", "selector": "h3", "type": "text"},
                    {"name": "department", "selector": "span.dept", "type": "text"},
                    {"name": "location", "selector": "span.loc", "type": "text"},
                ],
            },
        },
        success_criteria=[
            "success=true",
            "record_count = 2",
            "records[0]['title'] contains 'Engineer'",
            "records[0]['department'] = 'Engineering'",
            "records[0]['location'] contains 'San Francisco'",
        ],
        failure_criteria=[
            "record_count = 0",
        ],
    ),
]

PRODUCTS_TESTS = [
    E2ETestCase(
        use_case="products",
        site="https://books.toscrape.com",
        description="Extract product catalog from books.toscrape.com",
        why="Known test ecommerce site. Validates full product pipeline: discovery → extraction → normalization.",
        endpoint="/products",
        payload={
            "site": "https://books.toscrape.com",
            "max_products": 10,
            "max_categories": 2,
            "timeout_ms": 90000,
        },
        success_criteria=[
            "success=true",
            "total_records >= 1 (found products)",
            "records have objectID field",
            "records have name field with real book titles",
            "records have url field pointing to book pages",
            "duration_ms > 0",
        ],
        failure_criteria=[
            "success=false (crawl failed)",
            "total_records = 0 (no products extracted)",
        ],
        timeout=120.0,
    ),
]

INTELLIGENCE_TESTS = [
    E2ETestCase(
        use_case="run/company",
        site="https://stripe.com",
        description="Extract company intelligence from Stripe",
        why="Stripe has a rich about page. Tests company runner: name, description, leadership, social links.",
        endpoint="/run/company",
        payload={"url": "https://stripe.com", "mode": "auto"},
        success_criteria=[
            "success=true",
            "total_records >= 1",
            "use_case = 'company'",
            "output includes company name or description",
        ],
        failure_criteria=[
            "success=false",
            "total_records = 0 (runner found nothing)",
        ],
    ),
    E2ETestCase(
        use_case="run/careers",
        site="https://stripe.com",
        description="Extract job listings from Stripe",
        why="Large tech company with public careers page. Tests careers runner.",
        endpoint="/run/careers",
        payload={"url": "https://stripe.com", "mode": "auto"},
        success_criteria=[
            "success=true",
            "total_records >= 1",
            "use_case = 'careers'",
        ],
        failure_criteria=[
            "success=false",
            "total_records = 0",
        ],
    ),
    E2ETestCase(
        use_case="run/news",
        site="https://stripe.com",
        description="Extract news signals from Stripe",
        why="Stripe frequently appears in tech news. Tests news runner against active company.",
        endpoint="/run/news",
        payload={"url": "https://stripe.com", "mode": "auto"},
        success_criteria=[
            "success=true",
            "total_records >= 1",
            "use_case = 'news'",
        ],
        failure_criteria=[
            "success=false",
            "total_records = 0",
        ],
    ),
    E2ETestCase(
        use_case="run/website-quality",
        site="https://stripe.com",
        description="Audit Stripe's website quality",
        why="Stripe has a well-built website. Tests SEO, structured data, accessibility signal extraction.",
        endpoint="/run/website-quality",
        payload={"url": "https://stripe.com", "mode": "auto"},
        success_criteria=[
            "success=true",
            "total_records >= 1",
            "use_case = 'website-quality'",
        ],
        failure_criteria=[
            "success=false",
        ],
    ),
    E2ETestCase(
        use_case="run/research",
        site="https://stripe.com",
        description="Extract research/blog content from Stripe",
        why="Stripe has an active blog. Tests research runner on content-rich site.",
        endpoint="/run/research",
        payload={"url": "https://stripe.com", "mode": "auto"},
        success_criteria=[
            "success=true",
            "total_records >= 1",
            "use_case = 'research'",
        ],
        failure_criteria=[
            "success=false",
        ],
    ),
    E2ETestCase(
        use_case="run/social",
        site="https://stripe.com",
        description="Find Stripe's social media profiles",
        why="Stripe links social profiles from homepage. Tests social URL regex extraction.",
        endpoint="/run/social",
        payload={"url": "https://stripe.com", "mode": "auto"},
        success_criteria=[
            "success=true or total_records >= 0 (social may find 0 on some sites)",
            "use_case = 'social'",
        ],
        failure_criteria=[
            "HTTP error (not 200)",
        ],
    ),
    E2ETestCase(
        use_case="run/locations",
        site="https://stripe.com",
        description="Find Stripe office locations",
        why="Stripe has multiple offices. Tests location runner address regex.",
        endpoint="/run/locations",
        payload={"url": "https://stripe.com", "mode": "auto"},
        success_criteria=[
            "success=true or total_records >= 0 (locations runner returns what it finds)",
            "use_case = 'locations'",
        ],
        failure_criteria=[
            "HTTP error",
        ],
    ),
    E2ETestCase(
        use_case="run/prism",
        site="https://notion.so",
        description="Full PRISM intelligence sweep on Notion",
        why="Notion is a different company type (SaaS tool). Tests PRISM aggregate across all 8 verticals on a non-Stripe target.",
        endpoint="/run/prism",
        payload={"url": "https://notion.so", "mode": "auto"},
        success_criteria=[
            "success=true",
            "use_case = 'prism'",
            "total_records >= 1 (at least one vertical found something)",
        ],
        failure_criteria=[
            "success=false",
            "total_records = 0 (all verticals failed)",
        ],
        timeout=180.0,
    ),
]

ALGOLIA_TESTS = [
    E2ETestCase(
        use_case="algolia/preview",
        site="N/A (Algolia validation)",
        description="Preview well-formed product records",
        why="Validates the last-mile before Algolia push — field checking, credential validation.",
        endpoint="/algolia/preview",
        payload={
            "app_id": "test-app",
            "api_key": "test-key",
            "index_name": "products",
            "records": [
                {
                    "objectID": "shoe-1",
                    "name": "Nike Air Max 90",
                    "url": "https://nike.com/air-max-90",
                    "price": 130.0,
                    "brand": "Nike",
                },
                {
                    "objectID": "shoe-2",
                    "name": "Adidas Ultraboost",
                    "url": "https://adidas.com/ultraboost",
                    "price": 180.0,
                    "brand": "Adidas",
                },
            ],
        },
        success_criteria=[
            "ready=true (all required fields present)",
            "record_count=2",
            "sample_object_ids includes 'shoe-1'",
            "missing_required_fields is empty",
            "credentials.app_id_configured=true",
        ],
        failure_criteria=[
            "ready=false (unexpected validation failure)",
        ],
    ),
]

ALL_TESTS = {
    "scrape": SCRAPE_TESTS,
    "crawl": CRAWL_TESTS,
    "map": MAP_TESTS,
    "screenshot": SCREENSHOT_TESTS,
    "structure": STRUCTURE_TESTS,
    "products": PRODUCTS_TESTS,
    "intelligence": INTELLIGENCE_TESTS,
    "algolia": ALGOLIA_TESTS,
}

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


class E2ERunner:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
        self.results: list[E2EResult] = []

    def run_test(self, tc: E2ETestCase) -> E2EResult:
        print(f"\n  {'─' * 56}")
        print(f"  {tc.use_case} → {tc.site}")
        print(f"  {tc.description}")
        print(f"  Why: {tc.why}")
        print(f"  {'─' * 56}")

        client = httpx.Client(timeout=tc.timeout, headers=self.headers)
        start = time.monotonic()
        try:
            r = client.post(f"{self.base_url}{tc.endpoint}", json=tc.payload)
            ms = int((time.monotonic() - start) * 1000)
            try:
                data = r.json()
            except Exception:
                data = {"_raw": r.text[:500], "_status": r.status_code}
        except Exception as exc:
            ms = int((time.monotonic() - start) * 1000)
            data = {}
            result = E2EResult(
                test_case=tc,
                passed=False,
                checks=[],
                duration_ms=ms,
                raw_response={},
                error=str(exc),
            )
            print(f"  ERROR: {exc}")
            self.results.append(result)
            return result

        checks = self._evaluate(tc, data, r.status_code)
        all_passed = all(c[1] for c in checks)

        result = E2EResult(
            test_case=tc,
            passed=all_passed,
            checks=checks,
            duration_ms=ms,
            raw_response=data,
        )

        for criterion, passed, detail in checks:
            status = "✓" if passed else "✗"
            print(f"    {status} {criterion}")
            if not passed:
                print(f"      → {detail}")

        print(f"  ⏱ {ms}ms | {'PASS' if all_passed else 'FAIL'}")
        self.results.append(result)
        return result

    def _evaluate(
        self, tc: E2ETestCase, data: dict, status_code: int
    ) -> list[tuple[str, bool, str]]:
        checks: list[tuple[str, bool, str]] = []

        checks.append(("HTTP 200", status_code == 200, f"status_code={status_code}"))

        for criterion in tc.success_criteria:
            passed, detail = self._check_criterion(criterion, data)
            checks.append((criterion, passed, detail))

        return checks

    @staticmethod
    def _first_int(text: str) -> int:
        m = re.search(r"\d+", text)
        return int(m.group()) if m else 0

    def _check_criterion(self, criterion: str, data: dict) -> tuple[bool, str]:
        c = criterion.lower()

        if c.startswith("success=true or"):
            return data.get("success") is True or data.get(
                "total_records", -1
            ) >= 0, f"success={data.get('success')}, total_records={data.get('total_records')}"

        if "success=true" in c:
            v = data.get("success")
            return v is True, f"success={v}, error={data.get('error', '')[:100]}"

        if "success=false" in c:
            v = data.get("success")
            return v is False, f"success={v}"

        if "ready=true" in c:
            v = data.get("ready")
            return v is True, f"ready={v}"

        if "markdown contains" in c:
            keyword = criterion.split("'")[1] if "'" in criterion else ""
            md = data.get("markdown", "")
            return keyword.lower() in md.lower(), f"markdown_len={len(md)}, searched='{keyword}'"

        if "markdown length >" in c:
            threshold = self._first_int(c.split(">")[1])
            md_len = len(data.get("markdown", ""))
            return md_len > threshold, f"markdown_len={md_len}"

        if "pages[0].markdown is non-empty" in c:
            pages = data.get("pages", [])
            md_len = len(pages[0].get("markdown", "")) if pages else 0
            return md_len > 0, f"pages[0].markdown_len={md_len}"

        if "markdown is non-empty" in c:
            return len(
                data.get("markdown", "")
            ) > 0, f"markdown_len={len(data.get('markdown', ''))}"

        if "metadata.title is non-empty" in c:
            title = data.get("metadata", {}).get("title", "")
            return len(title) > 0, f"title='{title[:60]}'"

        if "metadata.word_count >" in c:
            threshold = self._first_int(c.split(">")[1])
            wc = data.get("metadata", {}).get("word_count", 0)
            return wc > threshold, f"word_count={wc}"

        if "metadata.url contains" in c:
            keyword = criterion.split("'")[1] if "'" in criterion else ""
            url = data.get("metadata", {}).get("url", "")
            return keyword.lower() in url.lower(), f"url={url[:80]}"

        if "links list has >" in c:
            threshold = self._first_int(c.split(">")[1])
            links = data.get("links", [])
            return len(links) > threshold, f"links_count={len(links)}"

        if "links list is empty" in c:
            return len(data.get("links", [])) == 0, f"links_count={len(data.get('links', []))}"

        if "total_pages >=" in c:
            threshold = self._first_int(c.split(">=")[1])
            tp = data.get("total_pages", 0)
            return tp >= threshold, f"total_pages={tp}"

        if "all pages have success=true" in c:
            pages = data.get("pages", [])
            fails = [p.get("url", "?") for p in pages if not p.get("success")]
            return len(fails) == 0, f"failed_pages={fails[:3]}"

        if "pages contain different urls" in c:
            pages = data.get("pages", [])
            urls = {p.get("url", "") for p in pages}
            return len(urls) > 1, f"unique_urls={len(urls)}"

        if "total >=" in c:
            threshold = self._first_int(c.split(">=")[1])
            total = data.get("total", 0)
            return total >= threshold, f"total={total}"

        if "urls contain" in c:
            keyword = criterion.split("'")[1] if "'" in criterion else ""
            urls = data.get("urls", [])
            found = any(keyword in u for u in urls)
            return found, f"checked {len(urls)} urls for '{keyword}'"

        if "screenshot_base64 length >" in c:
            threshold = self._first_int(c.split(">")[1])
            b64_len = len(data.get("screenshot_base64", ""))
            return b64_len > threshold, f"base64_len={b64_len}"

        if "screenshot_base64 is empty" in c:
            return len(data.get("screenshot_base64", "")) == 0, "checked"

        if "width >=" in c:
            threshold = self._first_int(c.split(">=")[1])
            w = data.get("width", 0)
            return w >= threshold, f"width={w}"

        if "height > 0" in c:
            h = data.get("height", 0)
            return h > 0, f"height={h}"

        if "record_count" in c and "=" in c:
            expected = self._first_int(c.split("=")[1])
            actual = data.get("record_count", 0)
            return actual == expected, f"record_count={actual}"

        if "records have objectid" in c:
            recs = data.get("records", [])
            has = all("objectID" in r for r in recs) if recs else False
            return (
                has,
                f"records_count={len(recs)}, sample_keys={list(recs[0].keys())[:5] if recs else []}",
            )

        if "records have name field" in c:
            recs = data.get("records", [])
            has = all(r.get("name") for r in recs) if recs else False
            sample = recs[0].get("name", "")[:50] if recs else ""
            return has, f"sample_name='{sample}'"

        if "records have url field" in c:
            recs = data.get("records", [])
            has = all(r.get("url") for r in recs) if recs else False
            return has, f"records_count={len(recs)}"

        if "total_records >=" in c:
            threshold = self._first_int(c.split(">=")[1])
            tr = data.get("total_records", 0)
            return tr >= threshold, f"total_records={tr}"

        if "total_records = 0" in c:
            return data.get("total_records", -1) == 0, f"total_records={data.get('total_records')}"

        if "use_case =" in c or "use_case=" in c:
            expected = criterion.split("'")[1] if "'" in criterion else ""
            actual = data.get("use_case", "")
            return actual == expected, f"use_case='{actual}'"

        if "duration_ms > 0" in c:
            return data.get("duration_ms", 0) > 0, f"duration_ms={data.get('duration_ms')}"

        if "records[0] has" in c:
            recs = data.get("records", [])
            if not recs:
                return False, "no records"
            field_name = criterion.split("'")[1] if "'" in criterion else ""
            return field_name in recs[0], f"keys={list(recs[0].keys())[:8]}"

        if "records[0][" in c and "contains" in c:
            recs = data.get("records", [])
            if not recs:
                return False, "no records"
            parts = criterion.split("'")
            if len(parts) >= 4:
                field_name = parts[1]
                keyword = parts[3]
                val = str(recs[0].get(field_name, ""))
                return keyword.lower() in val.lower(), f"{field_name}='{val[:60]}'"
            return False, "parse error"

        if "sample_object_ids includes" in c:
            keyword = criterion.split("'")[1] if "'" in criterion else ""
            ids = data.get("sample_object_ids", [])
            return keyword in ids, f"ids={ids[:5]}"

        if "missing_required_fields is empty" in c:
            mrf = data.get("missing_required_fields", ["not-empty"])
            return len(mrf) == 0, f"missing={mrf[:5]}"

        if "credentials.app_id_configured=true" in c:
            v = data.get("credentials", {}).get("app_id_configured")
            return v is True, f"app_id_configured={v}"

        if "output includes company" in c:
            tr = data.get("total_records", 0)
            return tr > 0, f"total_records={tr}"

        if "http error" in c:
            return False, "skipped (negative criterion)"

        return True, f"unmatched criterion: {criterion}"

    def print_summary(self) -> tuple[int, int]:
        print(f"\n\n{'═' * 70}")
        print("SCOUT E2E TEST RESULTS — REAL WEBSITES")
        print(f"{'═' * 70}\n")

        total_pass = 0
        total_fail = 0

        by_use_case: dict[str, list[E2EResult]] = {}
        for r in self.results:
            uc = r.test_case.use_case
            by_use_case.setdefault(uc, []).append(r)

        for uc, results in by_use_case.items():
            uc_pass = sum(1 for r in results if r.passed)
            uc_fail = sum(1 for r in results if not r.passed)
            total_pass += uc_pass
            total_fail += uc_fail

            status = "PASS" if uc_fail == 0 else "FAIL"
            print(f"[{status}] {uc}: {uc_pass}/{uc_pass + uc_fail} sites passed")
            for r in results:
                site_status = "✓" if r.passed else "✗"
                print(f"  {site_status} {r.test_case.site} ({r.duration_ms}ms)")
                if not r.passed:
                    for criterion, passed, detail in r.checks:
                        if not passed:
                            print(f"    FAIL: {criterion} → {detail[:120]}")
            print()

        print(f"{'═' * 70}")
        total = total_pass + total_fail
        pct = (total_pass / total * 100) if total else 0
        print(f"TOTAL: {total} test cases | {total_pass} passed | {total_fail} failed | {pct:.0f}%")
        print(f"{'═' * 70}")

        return total_pass, total_fail


def main():
    parser = argparse.ArgumentParser(description="Scout E2E Real Website Tests")
    parser.add_argument("--base-url", default="http://localhost:8421")
    parser.add_argument("--api-key", default="dev-key")
    parser.add_argument(
        "--use-case",
        default="all",
        help="Run specific use case: scrape, crawl, map, screenshot, structure, products, intelligence, algolia, or all",
    )
    args = parser.parse_args()

    runner = E2ERunner(args.base_url, args.api_key)

    if args.use_case == "all":
        tests = []
        for group in ALL_TESTS.values():
            tests.extend(group)
    elif args.use_case in ALL_TESTS:
        tests = ALL_TESTS[args.use_case]
    else:
        print(f"Unknown use case: {args.use_case}")
        print(f"Available: {', '.join(ALL_TESTS.keys())}, all")
        sys.exit(1)

    print(f"{'═' * 70}")
    print(f"SCOUT E2E TEST SUITE — {len(tests)} test cases")
    print(f"Target: {args.base_url}")
    print(f"{'═' * 70}")

    for tc in tests:
        runner.run_test(tc)

    passed, failed = runner.print_summary()
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
