"""Benchmark Scout acquisition against simple direct HTTP fetches."""

from __future__ import annotations

import asyncio
import json
import ssl
import time
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

from scout.core.modes.scrape import scrape
from scout.core.types import ScrapeRequest


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip += 1
        if tag in {"p", "li", "h1", "h2", "h3", "br", "section", "article"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip:
            self._skip -= 1
        if tag in {"p", "li", "h1", "h2", "h3", "section", "article"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(data)

    def text(self) -> str:
        return " ".join(" ".join(self.parts).split())


@dataclass(frozen=True)
class BenchmarkResult:
    url: str
    direct_http: dict
    scout: dict
    recommendation: str
    reason: str


def _word_count(text: str) -> int:
    return len((text or "").split())


def _ssl_context() -> ssl.SSLContext | None:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return None


def direct_http_fetch(url: str, timeout: int = 30) -> dict:
    started = time.time()
    request = Request(url, headers={"User-Agent": "ScoutBenchmark/1.0"})
    try:
        with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            raw = response.read(1_500_000)
            body = raw.decode(response.headers.get_content_charset() or "utf-8", errors="replace")
            if "<html" in body[:1000].lower() or "<body" in body[:5000].lower():
                parser = _TextExtractor()
                parser.feed(body)
                text = parser.text()
            else:
                text = " ".join(body.split())
            return {
                "success": True,
                "status_code": getattr(response, "status", 200),
                "duration_ms": int((time.time() - started) * 1000),
                "word_count": _word_count(text),
                "text": text,
                "error": "",
            }
    except Exception as exc:
        return {
            "success": False,
            "status_code": None,
            "duration_ms": int((time.time() - started) * 1000),
            "word_count": 0,
            "text": "",
            "error": str(exc),
        }


async def run_benchmark(url: str, *, use_js: bool = True, expected_markers: list[str] | None = None) -> BenchmarkResult:
    direct = direct_http_fetch(url)
    scout_resp = await scrape(
        ScrapeRequest(
            url=url,
            use_js=use_js,
            cleanup=True,
            quality_analysis=True,
            recommend_collector=True,
            expected_markers=expected_markers or [],
        )
    )
    scout_summary = {
        "success": scout_resp.success,
        "duration_ms": scout_resp.duration_ms,
        "word_count": scout_resp.metadata.word_count,
        "raw_markdown": scout_resp.raw_markdown or scout_resp.markdown,
        "clean_markdown": scout_resp.clean_markdown or scout_resp.markdown,
        "quality_score": scout_resp.acquisition.quality_score if scout_resp.acquisition else 0.0,
        "recommended_collector": scout_resp.acquisition.recommended_collector if scout_resp.acquisition else "",
        "response": scout_resp.model_dump(mode="json"),
    }
    recommendation = "scout_scrape"
    reason = "higher_quality_or_browser_needed"
    if direct["success"] and (not use_js) and direct["duration_ms"] < scout_resp.duration_ms:
        recommendation = "direct_http"
        reason = "faster_static_page"
    if scout_resp.acquisition and scout_resp.acquisition.recommended_collector == "rss_feed":
        recommendation = "rss_feed"
        reason = scout_resp.acquisition.recommended_collector_reason
    return BenchmarkResult(url=url, direct_http=direct, scout=scout_summary, recommendation=recommendation, reason=reason)


def write_benchmark_artifacts(result: BenchmarkResult, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "samples").mkdir(exist_ok=True)
    (output_dir / "benchmark.json").write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")
    (output_dir / "direct_http.txt").write_text(result.direct_http.get("text", ""), encoding="utf-8")
    (output_dir / "scout_raw.md").write_text(result.scout.get("raw_markdown", ""), encoding="utf-8")
    (output_dir / "scout_clean.md").write_text(result.scout.get("clean_markdown", ""), encoding="utf-8")
    comparison = f"""# Scout acquisition benchmark

URL: {result.url}

| Method | Success | Duration ms | Words |
|---|---:|---:|---:|
| direct_http | {result.direct_http.get('success')} | {result.direct_http.get('duration_ms')} | {result.direct_http.get('word_count')} |
| scout_scrape | {result.scout.get('success')} | {result.scout.get('duration_ms')} | {result.scout.get('word_count')} |

Recommendation: `{result.recommendation}`

Reason: {result.reason}
"""
    (output_dir / "comparison.md").write_text(comparison, encoding="utf-8")


def benchmark_sync(url: str, output_dir: Path, *, use_js: bool = True, expected_markers: list[str] | None = None) -> BenchmarkResult:
    result = asyncio.run(run_benchmark(url, use_js=use_js, expected_markers=expected_markers))
    write_benchmark_artifacts(result, output_dir)
    return result
