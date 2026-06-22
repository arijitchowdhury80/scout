"""Careers intelligence runner — scrapes careers/jobs pages for hiring signals."""

from __future__ import annotations

import re
from urllib.parse import urljoin

from scout.core.crawler import ScoutCrawler
from scout.core.platform.types import RunRequest
from scout.core.use_cases.intelligence import CareerSiteRecord
from scout.core.use_cases.runners.base import (
    evidence_from_scrape,
    make_citation,
    safe_scrape,
)

_CAREERS_PATHS = ["/careers", "/jobs", "/join-us", "/work-with-us", "/open-positions"]

_ATS_PATTERNS = {
    "greenhouse": re.compile(r"boards\.greenhouse\.io|greenhouse\.io", re.I),
    "lever": re.compile(r"jobs\.lever\.co|lever\.co/[\w-]+", re.I),
    "workday": re.compile(r"[\w-]+\.myworkdayjobs\.com|workday\.com", re.I),
    "icims": re.compile(r"careers-[\w]+\.icims\.com|icims\.com", re.I),
    "ashby": re.compile(r"jobs\.ashbyhq\.com", re.I),
    "bamboohr": re.compile(r"[\w-]+\.bamboohr\.com", re.I),
    "smartrecruiters": re.compile(r"jobs\.smartrecruiters\.com", re.I),
    "jobvite": re.compile(r"jobs\.jobvite\.com", re.I),
}

_DEPT_KEYWORDS = [
    "engineering",
    "product",
    "design",
    "marketing",
    "sales",
    "finance",
    "operations",
    "data",
    "support",
    "people",
    "hr",
    "legal",
    "security",
]


def _base_url(req: RunRequest) -> str:
    if req.url:
        return req.url.rstrip("/")
    if req.targets:
        return req.targets[0].rstrip("/")
    name = req.query.strip().lower().replace(" ", "")
    return f"https://www.{name}.com"


def _company_name(req: RunRequest) -> str:
    return req.query.strip() or "unknown"


def _detect_ats(all_text: str) -> str:
    for platform, pattern in _ATS_PATTERNS.items():
        if pattern.search(all_text):
            return platform
    return ""


def _extract_departments(markdown: str) -> list[str]:
    lower = markdown.lower()
    return [dept for dept in _DEPT_KEYWORDS if dept in lower]


def _count_job_signals(markdown: str) -> int:
    patterns = [
        re.compile(r"(?:open|available)\s+(?:positions?|roles?|jobs?)", re.I),
        re.compile(r"\b\d+\s+(?:open|available)\s+(?:positions?|roles?)", re.I),
    ]
    count = 0
    for p in patterns:
        count += len(p.findall(markdown))
    job_lines = re.findall(
        r"(?m)^.*(?:Engineer|Manager|Director|Analyst|Designer|Developer).*$", markdown
    )
    return count + len(job_lines)


async def run_careers(req: RunRequest, crawler: ScoutCrawler) -> list[dict]:
    base = _base_url(req)
    company = _company_name(req)
    slug = re.sub(r"[^a-z0-9]+", "_", company.lower()).strip("_")

    all_markdown = ""
    all_links: list[str] = []
    careers_url = ""
    source = None

    for path in _CAREERS_PATHS:
        url = urljoin(base + "/", path.lstrip("/"))
        resp = await safe_scrape(crawler, url)
        if resp:
            source = evidence_from_scrape(url, resp)
            careers_url = url
            all_markdown += resp.markdown + "\n"
            all_links.extend(resp.links)
            break

    if not source:
        return []

    all_text = all_markdown + "\n" + "\n".join(all_links)
    ats = _detect_ats(all_text)
    departments = _extract_departments(all_markdown)
    job_count = _count_job_signals(all_markdown)

    summary_parts = []
    if ats:
        summary_parts.append(f"ATS: {ats}")
    if departments:
        summary_parts.append(f"Departments: {', '.join(departments)}")
    if job_count:
        summary_parts.append(f"~{job_count} role signals detected")
    summary = "; ".join(summary_parts) or "Careers page found but no structured signals extracted."

    record = CareerSiteRecord(
        objectID=f"careers_{slug}",
        company=company,
        careers_url=careers_url,
        ats_platform=ats,
        departments=departments,
        hiring_signal_summary=summary,
        source_url=careers_url,
        confidence=0.75 if ats or departments else 0.5,
        citations=[make_citation(source, "careers_url", careers_url, summary[:200])],
    )
    return [record.model_dump(mode="json")]
