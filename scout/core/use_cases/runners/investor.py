"""Investor relations runner — scrapes IR pages for filings, reports, ticker."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from scout.core.crawler import ScoutCrawler
from scout.core.platform.types import RunRequest
from scout.core.use_cases.intelligence import InvestorAssetRecord
from scout.core.use_cases.runners.base import (
    evidence_from_scrape,
    make_citation,
    safe_scrape,
)

_IR_PATHS = [
    "/investor-relations",
    "/investors",
    "/ir",
    "/investor",
    "/shareholder-information",
]

_ASSET_PATTERNS = {
    "annual_report": re.compile(r"(?:annual[\s_-]?report|10[\s-]?K|yearly[\s_-]?report)", re.I),
    "quarterly_report": re.compile(r"(?:quarterly[\s_-]?report|10[\s-]?Q)", re.I),
    "earnings": re.compile(r"(?:earnings[\s_-]?(?:call|release|report))", re.I),
    "sec_filing": re.compile(r"(?:SEC[\s_-]?filing|proxy[\s_-]?statement|DEF[\s_-]?14)", re.I),
    "press_release": re.compile(r"(?:press[\s_-]?release|news[\s_-]?release)", re.I),
}

_TICKER_PATTERN = re.compile(r"(?:NYSE|NASDAQ|ticker|symbol)[:\s]+\(?([A-Z]{1,5})\)?", re.I)


def _base_url(req: RunRequest) -> str:
    if req.url:
        return req.url.rstrip("/")
    if req.targets:
        return req.targets[0].rstrip("/")
    name = req.query.strip().lower().replace(" ", "")
    return f"https://www.{name}.com"


def _company_name(req: RunRequest) -> str:
    return req.query.strip() or "unknown"


def _extract_ticker(markdown: str) -> str:
    match = _TICKER_PATTERN.search(markdown)
    return match.group(1) if match else ""


def _candidate_urls(base: str) -> list[str]:
    parsed = urlparse(base)
    root = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else base
    urls: list[str] = []
    if parsed.path and parsed.path != "/":
        urls.append(base)
    urls.extend(urljoin(root.rstrip("/") + "/", path.lstrip("/")) for path in _IR_PATHS)
    return list(dict.fromkeys(urls))


async def run_investor(req: RunRequest, crawler: ScoutCrawler) -> list[dict]:
    base = _base_url(req)
    company = _company_name(req)
    slug = re.sub(r"[^a-z0-9]+", "_", company.lower()).strip("_")

    all_markdown = ""
    all_links: list[str] = []
    ir_url = ""
    source = None

    for url in _candidate_urls(base):
        resp = await safe_scrape(crawler, url)
        if resp:
            source = evidence_from_scrape(url, resp)
            ir_url = url
            all_markdown += resp.markdown + "\n"
            all_links.extend(resp.links)
            break

    if not source:
        return []

    records: list[dict] = []
    ticker = _extract_ticker(all_markdown)

    ir_record = InvestorAssetRecord(
        objectID=f"investor_{slug}_page",
        company=company,
        asset_type="investor_page",
        url=ir_url,
        title=f"{company} investor relations" + (f" ({ticker})" if ticker else ""),
        source_url=ir_url,
        confidence=0.8,
        citations=[make_citation(source, "url", ir_url, f"IR page found at {ir_url}")],
    )
    records.append(ir_record.model_dump(mode="json"))

    all_text = all_markdown + "\n" + "\n".join(all_links)
    for asset_type, pattern in _ASSET_PATTERNS.items():
        if pattern.search(all_text):
            asset_id = f"investor_{slug}_{asset_type}"
            records.append(
                InvestorAssetRecord(
                    objectID=asset_id,
                    company=company,
                    asset_type=asset_type,
                    url=ir_url,
                    title=f"{company} {asset_type.replace('_', ' ')}",
                    source_url=ir_url,
                    confidence=0.65,
                    citations=[
                        make_citation(
                            source,
                            "asset_type",
                            asset_type,
                            f"{asset_type} reference found on IR page",
                        )
                    ],
                ).model_dump(mode="json")
            )

    return records
