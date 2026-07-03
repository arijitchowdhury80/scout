#!/usr/bin/env python3
"""Scout Endpoint Validation Suite.

Tests every public API endpoint against a running Scout instance.
For each endpoint: multiple queries, success/failure criteria, detailed reporting.

Usage:
    python tests/validate_endpoints.py [--base-url http://localhost:8421] [--api-key dev-key]
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass, field

import httpx

# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------


@dataclass
class TestResult:
    endpoint: str
    test_name: str
    passed: bool
    expected: str
    actual: str
    duration_ms: int = 0
    details: str = ""


@dataclass
class EndpointReport:
    endpoint: str
    use_case: str
    business_value: str
    results: list[TestResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------


class ScoutValidator:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
        self.client = httpx.Client(timeout=120.0, headers=self.headers)
        self.reports: list[EndpointReport] = []

    def _post(self, path: str, body: dict) -> tuple[int, dict, int]:
        start = time.monotonic()
        try:
            r = self.client.post(f"{self.base_url}{path}", json=body)
            ms = int((time.monotonic() - start) * 1000)
            try:
                data = r.json()
            except Exception:
                data = {"_raw": r.text[:500]}
            return r.status_code, data, ms
        except Exception as exc:
            ms = int((time.monotonic() - start) * 1000)
            return 0, {"_error": str(exc)}, ms

    def _get(self, path: str) -> tuple[int, dict, int]:
        start = time.monotonic()
        try:
            r = self.client.get(f"{self.base_url}{path}")
            ms = int((time.monotonic() - start) * 1000)
            try:
                data = r.json()
            except Exception:
                data = {"_raw": r.text[:500]}
            return r.status_code, data, ms
        except Exception as exc:
            ms = int((time.monotonic() - start) * 1000)
            return 0, {"_error": str(exc)}, ms

    def _assert(
        self,
        report: EndpointReport,
        name: str,
        expected: str,
        condition: bool,
        actual: str,
        ms: int = 0,
        details: str = "",
    ):
        report.results.append(
            TestResult(
                endpoint=report.endpoint,
                test_name=name,
                passed=condition,
                expected=expected,
                actual=actual,
                duration_ms=ms,
                details=details,
            )
        )
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {name} ({ms}ms)")
        if not condition:
            print(f"         expected: {expected}")
            print(f"         actual:   {actual[:200]}")

    # -----------------------------------------------------------------------
    # 1. GET /health
    # -----------------------------------------------------------------------
    def test_health(self):
        report = EndpointReport(
            endpoint="GET /health",
            use_case="Service liveness check",
            business_value="Monitoring, load balancer health probes, uptime verification",
        )
        print(f"\n{'=' * 60}\n{report.endpoint} — {report.use_case}\n{'=' * 60}")

        # No auth needed
        client_noauth = httpx.Client(timeout=10.0)
        start = time.monotonic()
        r = client_noauth.get(f"{self.base_url}/health")
        ms = int((time.monotonic() - start) * 1000)
        data = r.json()

        self._assert(
            report,
            "returns 200",
            "status_code=200",
            r.status_code == 200,
            f"status_code={r.status_code}",
            ms,
        )
        self._assert(
            report,
            "status is ok",
            "status='ok'",
            data.get("status") == "ok",
            f"status={data.get('status')}",
            ms,
        )
        self._assert(
            report,
            "has scout_version",
            "scout_version present",
            bool(data.get("scout_version")),
            f"scout_version={data.get('scout_version')}",
            ms,
        )
        self._assert(
            report,
            "has crawl4ai_version",
            "crawl4ai_version present",
            bool(data.get("crawl4ai_version")),
            f"crawl4ai_version={data.get('crawl4ai_version')}",
            ms,
        )

        self.reports.append(report)

    # -----------------------------------------------------------------------
    # 2. POST /scrape
    # -----------------------------------------------------------------------
    def test_scrape(self):
        report = EndpointReport(
            endpoint="POST /scrape",
            use_case="Single-page content extraction",
            business_value="Extract clean text from any URL for LLM consumption, research, monitoring",
        )
        print(f"\n{'=' * 60}\n{report.endpoint} — {report.use_case}\n{'=' * 60}")

        # Test 1: Simple static page
        code, data, ms = self._post("/scrape", {"url": "https://httpbin.org/html"})
        self._assert(
            report,
            "httpbin/html returns 200",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )
        self._assert(
            report,
            "httpbin/html success=true",
            "success=true",
            data.get("success") is True,
            f"success={data.get('success')}",
            ms,
        )
        self._assert(
            report,
            "httpbin/html has markdown",
            "markdown non-empty",
            len(data.get("markdown", "")) > 10,
            f"markdown_len={len(data.get('markdown', ''))}",
            ms,
        )
        self._assert(
            report,
            "httpbin/html has metadata",
            "metadata.url present",
            bool(data.get("metadata", {}).get("url")),
            f"metadata={data.get('metadata', {})}",
            ms,
        )

        # Test 2: Real website
        code, data, ms = self._post("/scrape", {"url": "https://example.com"})
        self._assert(
            report,
            "example.com returns 200",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )
        self._assert(
            report,
            "example.com success=true",
            "success=true",
            data.get("success") is True,
            f"success={data.get('success')}",
            ms,
        )
        self._assert(
            report,
            "example.com markdown has content",
            "markdown contains 'Example Domain'",
            "Example Domain" in data.get("markdown", ""),
            f"markdown_start={data.get('markdown', '')[:100]}",
            ms,
        )
        self._assert(
            report,
            "example.com has links",
            "links is a list",
            isinstance(data.get("links"), list),
            f"links_type={type(data.get('links'))}",
            ms,
        )

        # Test 3: Invalid URL
        code, data, ms = self._post(
            "/scrape", {"url": "https://this-domain-definitely-does-not-exist-12345.com"}
        )
        self._assert(
            report,
            "invalid domain returns 200 with error",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )
        self._assert(
            report,
            "invalid domain success=false",
            "success=false",
            data.get("success") is False,
            f"success={data.get('success')}",
            ms,
        )

        # Test 4: With raw HTML format
        code, data, ms = self._post(
            "/scrape", {"url": "https://example.com", "formats": ["markdown", "raw_html"]}
        )
        self._assert(
            report,
            "multi-format returns raw_html",
            "raw_html non-empty",
            len(data.get("raw_html", "")) > 10,
            f"raw_html_len={len(data.get('raw_html', ''))}",
            ms,
        )

        self.reports.append(report)

    # -----------------------------------------------------------------------
    # 3. POST /crawl
    # -----------------------------------------------------------------------
    def test_crawl(self):
        report = EndpointReport(
            endpoint="POST /crawl",
            use_case="Multi-page site crawl",
            business_value="Index entire sites for knowledge bases, documentation scraping, content audit",
        )
        print(f"\n{'=' * 60}\n{report.endpoint} — {report.use_case}\n{'=' * 60}")

        # Test 1: Small site crawl
        code, data, ms = self._post(
            "/crawl", {"url": "https://example.com", "max_depth": 1, "max_pages": 3}
        )
        self._assert(
            report,
            "example.com returns 200",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )
        self._assert(
            report,
            "success=true",
            "success=true",
            data.get("success") is True,
            f"success={data.get('success')}",
            ms,
        )
        self._assert(
            report,
            "has pages list",
            "pages is list",
            isinstance(data.get("pages"), list),
            f"pages_type={type(data.get('pages'))}",
            ms,
        )
        self._assert(
            report,
            "total_pages >= 1",
            "total_pages >= 1",
            data.get("total_pages", 0) >= 1,
            f"total_pages={data.get('total_pages')}",
            ms,
        )
        self._assert(
            report,
            "has duration_ms",
            "duration_ms > 0",
            data.get("duration_ms", 0) > 0,
            f"duration_ms={data.get('duration_ms')}",
            ms,
        )

        # Test 2: Crawl with URL pattern filter
        code, data, ms = self._post(
            "/crawl",
            {
                "url": "https://httpbin.org",
                "max_depth": 1,
                "max_pages": 5,
                "url_pattern": ".*html.*",
            },
        )
        self._assert(
            report,
            "pattern-filtered crawl returns 200",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )
        self._assert(
            report,
            "pattern-filtered success",
            "success=true",
            data.get("success") is True,
            f"success={data.get('success')}",
            ms,
        )

        self.reports.append(report)

    # -----------------------------------------------------------------------
    # 4. POST /map
    # -----------------------------------------------------------------------
    def test_map(self):
        report = EndpointReport(
            endpoint="POST /map",
            use_case="URL discovery (sitemap)",
            business_value="Discover all pages on a site before selective crawling — saves bandwidth",
        )
        print(f"\n{'=' * 60}\n{report.endpoint} — {report.use_case}\n{'=' * 60}")

        # Test 1: Map a simple site
        code, data, ms = self._post("/map", {"url": "https://example.com", "max_pages": 20})
        self._assert(
            report,
            "example.com returns 200",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )
        self._assert(
            report,
            "success=true",
            "success=true",
            data.get("success") is True,
            f"success={data.get('success')}",
            ms,
        )
        self._assert(
            report,
            "urls is list",
            "urls is list",
            isinstance(data.get("urls"), list),
            f"urls_type={type(data.get('urls'))}",
            ms,
        )
        self._assert(
            report,
            "total >= 1",
            "total >= 1",
            data.get("total", 0) >= 1,
            f"total={data.get('total')}",
            ms,
        )
        self._assert(
            report,
            "start_url populated",
            "start_url present",
            bool(data.get("start_url")),
            f"start_url={data.get('start_url')}",
            ms,
        )

        # Test 2: Map httpbin
        code, data, ms = self._post("/map", {"url": "https://httpbin.org", "max_pages": 10})
        self._assert(
            report, "httpbin returns 200", "status_code=200", code == 200, f"status_code={code}", ms
        )
        self._assert(
            report,
            "httpbin has URLs",
            "total >= 1",
            data.get("total", 0) >= 1,
            f"total={data.get('total')}",
            ms,
        )

        self.reports.append(report)

    # -----------------------------------------------------------------------
    # 5. POST /extract
    # -----------------------------------------------------------------------
    def test_extract(self):
        report = EndpointReport(
            endpoint="POST /extract",
            use_case="Structured data extraction with LLM/CSS",
            business_value="Pull typed records from pages — prices, contacts, job listings — for databases",
        )
        print(f"\n{'=' * 60}\n{report.endpoint} — {report.use_case}\n{'=' * 60}")

        # Test 1: CSS-based extraction on httpbin
        css_schema = {
            "baseSelector": "div.container",
            "fields": [
                {"name": "text", "selector": "p", "type": "text"},
            ],
        }
        code, data, ms = self._post(
            "/extract",
            {
                "url": "https://httpbin.org/html",
                "css_schema": css_schema,
            },
        )
        self._assert(
            report,
            "css extract returns 200",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )
        self._assert(
            report,
            "css extract success",
            "success=true",
            data.get("success") is True,
            f"success={data.get('success')}, error={data.get('error', '')}",
            ms,
        )

        # Test 2: Extract with instruction (LLM) — may fail without LLM key
        code, data, ms = self._post(
            "/extract",
            {
                "url": "https://example.com",
                "instruction": "Extract the main heading and description",
                "extraction_schema": {
                    "type": "object",
                    "properties": {
                        "heading": {"type": "string"},
                        "description": {"type": "string"},
                    },
                },
            },
        )
        self._assert(
            report,
            "llm extract returns 200",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )
        # LLM extract may fail without API key — that's expected
        if data.get("success"):
            self._assert(
                report,
                "llm extract has data",
                "data non-empty",
                bool(data.get("data")),
                f"data={data.get('data')}",
                ms,
            )
        else:
            self._assert(
                report,
                "llm extract fails gracefully",
                "error message present",
                bool(data.get("error")),
                f"error={data.get('error', 'none')}",
                ms,
                details="Expected: LLM key may not be configured",
            )

        self.reports.append(report)

    # -----------------------------------------------------------------------
    # 6. POST /structure
    # -----------------------------------------------------------------------
    def test_structure(self):
        report = EndpointReport(
            endpoint="POST /structure",
            use_case="Structure pre-fetched HTML (no network fetch)",
            business_value="Process captured HTML without re-triggering bot walls — PRISM integration",
        )
        print(f"\n{'=' * 60}\n{report.endpoint} — {report.use_case}\n{'=' * 60}")

        sample_html = """
        <html><head><title>Test Page</title></head>
        <body>
            <h1>Product Listing</h1>
            <div class="product">
                <h2>Widget A</h2>
                <p class="price">$29.99</p>
                <p class="desc">A fine widget</p>
            </div>
            <div class="product">
                <h2>Widget B</h2>
                <p class="price">$49.99</p>
                <p class="desc">A better widget</p>
            </div>
        </body></html>
        """

        # Test 1: Basic HTML to markdown
        code, data, ms = self._post(
            "/structure", {"html": sample_html, "source_url": "https://example.com/products"}
        )
        self._assert(
            report,
            "basic structure returns 200",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )
        self._assert(
            report,
            "success=true",
            "success=true",
            data.get("success") is True,
            f"success={data.get('success')}, error={data.get('error')}",
            ms,
        )
        self._assert(
            report,
            "markdown has content",
            "markdown non-empty",
            len(data.get("markdown", "")) > 10,
            f"markdown_len={len(data.get('markdown', ''))}",
            ms,
        )
        self._assert(
            report,
            "word_count > 0",
            "word_count > 0",
            data.get("word_count", 0) > 0,
            f"word_count={data.get('word_count')}",
            ms,
        )

        # Test 2: With CSS schema for typed records
        code, data, ms = self._post(
            "/structure",
            {
                "html": sample_html,
                "source_url": "https://example.com/products",
                "css_schema": {
                    "baseSelector": "div.product",
                    "fields": [
                        {"name": "name", "selector": "h2", "type": "text"},
                        {"name": "price", "selector": "p.price", "type": "text"},
                        {"name": "description", "selector": "p.desc", "type": "text"},
                    ],
                },
            },
        )
        self._assert(
            report,
            "css schema returns 200",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )
        self._assert(
            report,
            "css schema success",
            "success=true",
            data.get("success") is True,
            f"success={data.get('success')}, error={data.get('error')}",
            ms,
        )
        self._assert(
            report,
            "has records",
            "record_count >= 1",
            data.get("record_count", 0) >= 1,
            f"record_count={data.get('record_count')}",
            ms,
        )
        if data.get("records"):
            rec = data["records"][0]
            self._assert(
                report,
                "record has name field",
                "name in record",
                "name" in rec,
                f"record_keys={list(rec.keys())}",
                ms,
            )

        # Test 3: Empty HTML
        code, data, ms = self._post("/structure", {"html": ""})
        self._assert(
            report,
            "empty html returns 200",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )

        self.reports.append(report)

    # -----------------------------------------------------------------------
    # 7. POST /screenshot
    # -----------------------------------------------------------------------
    def test_screenshot(self):
        report = EndpointReport(
            endpoint="POST /screenshot",
            use_case="Visual page capture",
            business_value="Screenshot evidence for audits, visual regression, competitive analysis",
        )
        print(f"\n{'=' * 60}\n{report.endpoint} — {report.use_case}\n{'=' * 60}")

        # Test 1: Screenshot of example.com
        code, data, ms = self._post("/screenshot", {"url": "https://example.com"})
        self._assert(
            report,
            "example.com returns 200",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )
        self._assert(
            report,
            "success=true",
            "success=true",
            data.get("success") is True,
            f"success={data.get('success')}, error={data.get('error', '')}",
            ms,
        )
        self._assert(
            report,
            "has base64 data",
            "screenshot_base64 non-empty",
            len(data.get("screenshot_base64", "")) > 100,
            f"base64_len={len(data.get('screenshot_base64', ''))}",
            ms,
        )
        self._assert(
            report,
            "has dimensions",
            "width > 0 and height > 0",
            data.get("width", 0) > 0 and data.get("height", 0) > 0,
            f"width={data.get('width')}, height={data.get('height')}",
            ms,
        )

        # Test 2: Custom viewport
        code, data, ms = self._post(
            "/screenshot",
            {"url": "https://example.com", "viewport_width": 375, "viewport_height": 812},
        )
        self._assert(
            report,
            "mobile viewport returns 200",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )
        if data.get("success"):
            self._assert(
                report,
                "mobile width correct",
                "width ~375",
                abs(data.get("width", 0) - 375) < 50,
                f"width={data.get('width')}",
                ms,
            )

        self.reports.append(report)

    # -----------------------------------------------------------------------
    # 8. POST /products
    # -----------------------------------------------------------------------
    def test_products(self):
        report = EndpointReport(
            endpoint="POST /products",
            use_case="Product catalog extraction",
            business_value="Build Algolia-ready product records from any ecommerce site — core Scout use case",
        )
        print(f"\n{'=' * 60}\n{report.endpoint} — {report.use_case}\n{'=' * 60}")

        # Test 1: Small product crawl — use a simple, fast site
        code, data, ms = self._post(
            "/products",
            {
                "site": "https://books.toscrape.com",
                "max_products": 5,
                "max_categories": 1,
                "timeout_ms": 60000,
            },
        )
        self._assert(
            report,
            "books.toscrape returns 200",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )
        self._assert(
            report,
            "success field present",
            "success in response",
            "success" in data,
            f"keys={list(data.keys())[:10]}",
            ms,
        )
        self._assert(
            report,
            "has records list",
            "records is list",
            isinstance(data.get("records"), list),
            f"records_type={type(data.get('records'))}",
            ms,
        )
        self._assert(
            report,
            "has total_records",
            "total_records present",
            "total_records" in data,
            f"total_records={data.get('total_records')}",
            ms,
        )
        self._assert(
            report,
            "has duration_ms",
            "duration_ms > 0",
            data.get("duration_ms", 0) > 0,
            f"duration_ms={data.get('duration_ms')}",
            ms,
        )

        if data.get("records"):
            rec = data["records"][0]
            self._assert(
                report,
                "record has objectID",
                "objectID present",
                "objectID" in rec,
                f"keys={list(rec.keys())[:8]}",
                ms,
            )
            self._assert(
                report,
                "record has name",
                "name present",
                bool(rec.get("name")),
                f"name={rec.get('name', '')[:50]}",
                ms,
            )
            self._assert(
                report,
                "record has url",
                "url present",
                bool(rec.get("url")),
                f"url={rec.get('url', '')[:80]}",
                ms,
            )

        # Test 2: Missing site
        code, data, ms = self._post("/products", {"site": "", "max_products": 1})
        self._assert(
            report, "empty site handled", "status_code=200", code == 200, f"status_code={code}", ms
        )

        self.reports.append(report)

    # -----------------------------------------------------------------------
    # 9. POST /run/{use_case} — all intelligence verticals
    # -----------------------------------------------------------------------
    def test_run_use_cases(self):
        use_cases = [
            (
                "company",
                "https://stripe.com",
                "Company profile extraction — about page, leadership, founding info",
            ),
            (
                "careers",
                "https://stripe.com",
                "Job listings extraction — open roles, departments, locations",
            ),
            (
                "investor",
                "https://stripe.com",
                "Investor relations — exec quotes, SEC filings, financial signals",
            ),
            (
                "news",
                "https://stripe.com",
                "News signals — press releases, media mentions, recent events",
            ),
            (
                "research",
                "https://stripe.com",
                "Research content — blog posts, whitepapers, technical docs",
            ),
            (
                "social",
                "https://stripe.com",
                "Social media presence — LinkedIn, Twitter, Facebook profiles",
            ),
            (
                "locations",
                "https://stripe.com",
                "Office locations — addresses, phone numbers, coordinates",
            ),
        ]

        for uc, url, description in use_cases:
            report = EndpointReport(
                endpoint=f"POST /run/{uc}",
                use_case=uc,
                business_value=description,
            )
            print(f"\n{'=' * 60}\n{report.endpoint} — {report.use_case}\n{'=' * 60}")

            code, data, ms = self._post(f"/run/{uc}", {"url": url, "mode": "auto"})
            self._assert(
                report,
                f"{uc} returns 200",
                "status_code=200",
                code == 200,
                f"status_code={code}",
                ms,
            )
            self._assert(
                report,
                f"{uc} has success field",
                "success in response",
                "success" in data,
                f"keys={list(data.keys())}",
                ms,
            )
            self._assert(
                report,
                f"{uc} has use_case",
                "use_case matches",
                data.get("use_case") == uc,
                f"use_case={data.get('use_case')}",
                ms,
            )
            self._assert(
                report,
                f"{uc} has total_records",
                "total_records present",
                "total_records" in data,
                f"total_records={data.get('total_records')}",
                ms,
            )

            if data.get("success"):
                self._assert(
                    report,
                    f"{uc} records > 0",
                    "total_records > 0",
                    data.get("total_records", 0) > 0,
                    f"total_records={data.get('total_records')}",
                    ms,
                )
            else:
                has_info = bool(data.get("error")) or data.get("total_records", -1) == 0
                self._assert(
                    report,
                    f"{uc} has error or 0 records",
                    "error or total_records=0",
                    has_info,
                    f"error={data.get('error', '')[:100]}, total_records={data.get('total_records')}",
                    ms,
                    details="Runner may return 0 records for some sites",
                )

            self.reports.append(report)

    # -----------------------------------------------------------------------
    # 10. POST /run/prism — bounded PRISM V1 bundle
    # -----------------------------------------------------------------------
    def test_run_prism(self):
        report = EndpointReport(
            endpoint="POST /run/prism",
            use_case="PRISM aggregate intelligence",
            business_value=(
                "Run the bounded PRISM V1 prospect-intelligence bundle — "
                "company/social, careers, investor, and news"
            ),
        )
        print(f"\n{'=' * 60}\n{report.endpoint} — {report.use_case}\n{'=' * 60}")

        code, data, ms = self._post("/run/prism", {"url": "https://example.com", "mode": "auto"})
        self._assert(
            report, "prism returns 200", "status_code=200", code == 200, f"status_code={code}", ms
        )
        self._assert(
            report,
            "has success field",
            "success in response",
            "success" in data,
            f"keys={list(data.keys())}",
            ms,
        )
        self._assert(
            report,
            "use_case=prism",
            "use_case=prism",
            data.get("use_case") == "prism",
            f"use_case={data.get('use_case')}",
            ms,
        )

        self.reports.append(report)

    # -----------------------------------------------------------------------
    # 11. GET /runs/{run_id} (artifact lookup)
    # -----------------------------------------------------------------------
    def test_runs_lookup(self):
        report = EndpointReport(
            endpoint="GET /runs/{run_id}",
            use_case="Run result retrieval",
            business_value="Fetch results of completed runs — records, sources, artifacts",
        )
        print(f"\n{'=' * 60}\n{report.endpoint} — {report.use_case}\n{'=' * 60}")

        # First create a run to look up
        _, run_data, _ = self._post("/run/company", {"url": "https://example.com", "mode": "auto"})
        run_id = ""
        if run_data.get("manifest"):
            run_id = run_data["manifest"].get("run_id", "")

        if run_id:
            # Test run summary
            code, data, ms = self._get(f"/runs/{run_id}")
            self._assert(
                report,
                "run summary returns 200",
                "status_code=200",
                code == 200,
                f"status_code={code}",
                ms,
            )

            # Test records endpoint
            code, data, ms = self._get(f"/runs/{run_id}/records")
            self._assert(
                report,
                "records returns 200",
                "status_code=200",
                code == 200,
                f"status_code={code}",
                ms,
            )
            self._assert(
                report,
                "records has run_id",
                "run_id matches",
                data.get("run_id") == run_id,
                f"run_id={data.get('run_id')}",
                ms,
            )

            # Test sources endpoint
            code, data, ms = self._get(f"/runs/{run_id}/sources")
            self._assert(
                report,
                "sources returns 200",
                "status_code=200",
                code == 200,
                f"status_code={code}",
                ms,
            )

            # Test artifacts endpoint
            code, data, ms = self._get(f"/runs/{run_id}/artifacts")
            self._assert(
                report,
                "artifacts returns 200",
                "status_code=200",
                code == 200,
                f"status_code={code}",
                ms,
            )
        else:
            self._assert(
                report,
                "run created for lookup",
                "run_id present",
                False,
                f"no run_id from /run/company: {run_data.get('error', 'unknown')}",
                0,
            )

        # Test non-existent run
        code, data, ms = self._get("/runs/nonexistent-run-id-12345")
        self._assert(
            report,
            "missing run returns 404",
            "status_code=404",
            code == 404,
            f"status_code={code}",
            ms,
        )

        self.reports.append(report)

    # -----------------------------------------------------------------------
    # 12. POST /algolia/preview
    # -----------------------------------------------------------------------
    def test_algolia_preview(self):
        report = EndpointReport(
            endpoint="POST /algolia/preview",
            use_case="Algolia record validation",
            business_value="Validate records before push — catch missing fields, bad credentials early",
        )
        print(f"\n{'=' * 60}\n{report.endpoint} — {report.use_case}\n{'=' * 60}")

        # Test 1: Valid records
        code, data, ms = self._post(
            "/algolia/preview",
            {
                "app_id": "test-app-id",
                "api_key": "test-api-key",
                "index_name": "test_index",
                "records": [
                    {"objectID": "1", "name": "Widget", "url": "https://example.com/widget"},
                    {"objectID": "2", "name": "Gadget", "url": "https://example.com/gadget"},
                ],
            },
        )
        self._assert(
            report,
            "valid preview returns 200",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )
        self._assert(
            report,
            "ready=true",
            "ready=true",
            data.get("ready") is True,
            f"ready={data.get('ready')}",
            ms,
        )
        self._assert(
            report,
            "record_count=2",
            "record_count=2",
            data.get("record_count") == 2,
            f"record_count={data.get('record_count')}",
            ms,
        )
        self._assert(
            report,
            "credentials configured",
            "both configured",
            data.get("credentials", {}).get("app_id_configured") is True,
            f"credentials={data.get('credentials')}",
            ms,
        )

        # Test 2: Missing required fields
        code, data, ms = self._post(
            "/algolia/preview",
            {
                "app_id": "",
                "api_key": "",
                "index_name": "",
                "records": [{"objectID": "1"}],
            },
        )
        self._assert(
            report,
            "missing fields returns 200",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )
        self._assert(
            report,
            "ready=false",
            "ready=false",
            data.get("ready") is False,
            f"ready={data.get('ready')}",
            ms,
        )
        self._assert(
            report,
            "missing_required_fields populated",
            "missing fields listed",
            len(data.get("missing_required_fields", [])) > 0,
            f"missing={data.get('missing_required_fields')}",
            ms,
        )

        # Test 3: Empty records
        code, data, ms = self._post(
            "/algolia/preview",
            {
                "app_id": "x",
                "api_key": "y",
                "index_name": "z",
                "records": [],
            },
        )
        self._assert(
            report,
            "empty records handled",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )
        self._assert(
            report,
            "empty records not ready",
            "ready=false",
            data.get("ready") is False,
            f"ready={data.get('ready')}",
            ms,
        )

        self.reports.append(report)

    # -----------------------------------------------------------------------
    # 13. POST /algolia/push (dry — will fail with test credentials)
    # -----------------------------------------------------------------------
    def test_algolia_push(self):
        report = EndpointReport(
            endpoint="POST /algolia/push",
            use_case="Algolia record ingestion",
            business_value="Push extracted records to Algolia search index — final pipeline step",
        )
        print(f"\n{'=' * 60}\n{report.endpoint} — {report.use_case}\n{'=' * 60}")

        # Test 1: Push with fake credentials — should fail gracefully
        code, data, ms = self._post(
            "/algolia/push",
            {
                "app_id": "fake-app-id",
                "api_key": "fake-api-key",
                "index_name": "test_index",
                "records": [{"objectID": "1", "name": "Widget"}],
            },
        )
        self._assert(
            report,
            "fake creds returns 200",
            "status_code=200",
            code == 200,
            f"status_code={code}",
            ms,
        )
        self._assert(
            report,
            "success=false with fake creds",
            "success=false",
            data.get("success") is False,
            f"success={data.get('success')}",
            ms,
        )
        self._assert(
            report,
            "has error message",
            "errors non-empty",
            len(data.get("errors", [])) > 0,
            f"errors={data.get('errors')}",
            ms,
        )

        # Test 2: Empty records — should fail validation
        code, data, ms = self._post(
            "/algolia/push",
            {
                "app_id": "x",
                "api_key": "y",
                "index_name": "z",
                "records": [],
            },
        )
        self._assert(
            report,
            "empty records returns 422",
            "status_code=422",
            code == 422,
            f"status_code={code}",
            ms,
        )

        # Test 3: Missing fields — should fail validation
        code, data, ms = self._post(
            "/algolia/push",
            {
                "app_id": "",
                "api_key": "y",
                "index_name": "z",
                "records": [{"objectID": "1"}],
            },
        )
        self._assert(
            report,
            "blank app_id returns 422",
            "status_code=422",
            code == 422,
            f"status_code={code}",
            ms,
        )

        self.reports.append(report)

    # -----------------------------------------------------------------------
    # 14. POST /harvest (needs CDP — test error handling)
    # -----------------------------------------------------------------------
    def test_harvest(self):
        report = EndpointReport(
            endpoint="POST /harvest",
            use_case="Live browser tab extraction via CDP",
            business_value="Extract from already-open browser tabs — bypass bot walls, capture dynamic content",
        )
        print(f"\n{'=' * 60}\n{report.endpoint} — {report.use_case}\n{'=' * 60}")

        # Test: No CDP server running — should fail gracefully
        code, data, ms = self._post(
            "/harvest",
            {
                "cdp_url": "http://127.0.0.1:9222",
                "url": "https://example.com",
            },
        )
        self._assert(
            report, "no CDP returns 200", "status_code=200", code == 200, f"status_code={code}", ms
        )
        self._assert(
            report,
            "success=false without CDP",
            "success=false",
            data.get("success") is False,
            f"success={data.get('success')}",
            ms,
        )
        self._assert(
            report,
            "error explains CDP failure",
            "error non-empty",
            bool(data.get("error")),
            f"error={data.get('error', '')[:100]}",
            ms,
        )

        self.reports.append(report)

    # -----------------------------------------------------------------------
    # 15. Auth enforcement
    # -----------------------------------------------------------------------
    def test_auth_enforcement(self):
        report = EndpointReport(
            endpoint="AUTH middleware",
            use_case="API key authentication",
            business_value="Prevents unauthorized access to all endpoints",
        )
        print(f"\n{'=' * 60}\n{report.endpoint} — {report.use_case}\n{'=' * 60}")

        client_noauth = httpx.Client(timeout=10.0)

        # Test 1: /scrape without key
        start = time.monotonic()
        r = client_noauth.post(
            f"{self.base_url}/scrape",
            json={"url": "https://example.com"},
            headers={"Content-Type": "application/json"},
        )
        ms = int((time.monotonic() - start) * 1000)
        self._assert(
            report,
            "/scrape without key returns 401/403",
            "status_code in {401,403}",
            r.status_code in (401, 403),
            f"status_code={r.status_code}",
            ms,
        )

        # Test 2: /health without key — should still work
        r = client_noauth.get(f"{self.base_url}/health")
        self._assert(
            report,
            "/health without key returns 200",
            "status_code=200",
            r.status_code == 200,
            f"status_code={r.status_code}",
        )

        # Test 3: Wrong API key
        r = client_noauth.post(
            f"{self.base_url}/scrape",
            json={"url": "https://example.com"},
            headers={"X-API-Key": "wrong-key", "Content-Type": "application/json"},
        )
        self._assert(
            report,
            "wrong key returns 401/403",
            "status_code in {401,403}",
            r.status_code in (401, 403),
            f"status_code={r.status_code}",
        )

        self.reports.append(report)

    # -----------------------------------------------------------------------
    # Final report
    # -----------------------------------------------------------------------
    def print_report(self) -> tuple[int, int]:
        total_pass = 0
        total_fail = 0

        print(f"\n\n{'#' * 70}")
        print("SCOUT ENDPOINT VALIDATION REPORT")
        print(f"{'#' * 70}\n")

        for report in self.reports:
            status = "PASS" if report.failed == 0 else "FAIL"
            print(f"[{status}] {report.endpoint}")
            print(f"  Use case: {report.use_case}")
            print(f"  Business value: {report.business_value}")
            print(f"  Tests: {report.passed}/{report.passed + report.failed} passed")
            if report.failed > 0:
                for r in report.results:
                    if not r.passed:
                        print(f"    FAIL: {r.test_name}")
                        print(f"      expected: {r.expected}")
                        print(f"      actual:   {r.actual[:150]}")
                        if r.details:
                            print(f"      note:     {r.details}")
            print()
            total_pass += report.passed
            total_fail += report.failed

        print(f"{'=' * 70}")
        print(f"TOTAL: {total_pass + total_fail} tests | {total_pass} passed | {total_fail} failed")
        pct = (total_pass / (total_pass + total_fail) * 100) if (total_pass + total_fail) else 0
        print(f"PASS RATE: {pct:.1f}%")
        print(f"{'=' * 70}")

        return total_pass, total_fail

    def run_all(self) -> tuple[int, int]:
        """Run all endpoint tests and return (passed, failed)."""
        self.test_health()
        self.test_auth_enforcement()
        self.test_scrape()
        self.test_crawl()
        self.test_map()
        self.test_extract()
        self.test_structure()
        self.test_screenshot()
        self.test_products()
        self.test_run_use_cases()
        self.test_run_prism()
        self.test_runs_lookup()
        self.test_algolia_preview()
        self.test_algolia_push()
        self.test_harvest()
        return self.print_report()


def main():
    parser = argparse.ArgumentParser(description="Scout Endpoint Validation Suite")
    parser.add_argument("--base-url", default="http://localhost:8421", help="Scout base URL")
    parser.add_argument("--api-key", default="dev-key", help="Scout API key")
    args = parser.parse_args()

    validator = ScoutValidator(args.base_url, args.api_key)
    passed, failed = validator.run_all()
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
