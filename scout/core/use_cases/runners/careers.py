"""Careers intelligence runner — scrapes careers/jobs pages for hiring signals."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse

from scout.core.crawler import ScoutCrawler
from scout.core.platform.types import RunRequest
from scout.core.use_cases.intelligence import CareerRoleRecord, CareerSiteRecord
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


def _candidate_urls(base: str) -> list[str]:
    parsed = urlparse(base)
    root = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else base
    urls: list[str] = []
    if parsed.path and parsed.path != "/":
        urls.append(base)
    urls.extend(urljoin(root.rstrip("/") + "/", path.lstrip("/")) for path in _CAREERS_PATHS)
    return list(dict.fromkeys(urls))


def _detect_ats(all_text: str) -> str:
    for platform, pattern in _ATS_PATTERNS.items():
        if pattern.search(all_text):
            return platform
    return ""


def _extract_departments(markdown: str) -> list[str]:
    lower = markdown.lower()
    return [dept for dept in _DEPT_KEYWORDS if dept in lower]


_ROLE_LINE_RE = re.compile(
    r"(?m)^.*(?:Engineer|Manager|Director|Analyst|Designer|Developer|Specialist|Lead).*$"
)


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


# ---------------------------------------------------------------------------
# FX-11 Build 3 — 24h jobs filter
#
# Careers pages rarely link individually to each role from the landing
# page, so roles are detected line-by-line from rendered markdown (the same
# heuristic _count_job_signals already uses). Dates, when present, tend to
# appear on the same line ("Posted 3 days ago", "Posted today", or an
# explicit date). When no date is found, the role is never dropped and
# never assigned a guessed date — it's flagged instead. See
# CareerRoleRecord docstring.
# ---------------------------------------------------------------------------

_RELATIVE_POSTED_RE = re.compile(r"posted\s+(\d+)\s+(day|days|hour|hours|week|weeks)\s+ago", re.I)
_POSTED_TODAY_RE = re.compile(r"posted\s+today", re.I)
_ISO_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

_RELATIVE_UNIT_TO_TIMEDELTA = {
    "day": lambda n: timedelta(days=n),
    "days": lambda n: timedelta(days=n),
    "hour": lambda n: timedelta(hours=n),
    "hours": lambda n: timedelta(hours=n),
    "week": lambda n: timedelta(weeks=n),
    "weeks": lambda n: timedelta(weeks=n),
}


def _parse_posted_at(line: str, now: datetime) -> tuple[str | None, bool, str]:
    """Best-effort publish-date extraction from one role listing line.

    Returns (posted_at_iso, found, reason). found is False — and reason is
    a non-empty machine-readable code — whenever no recognizable date
    signal is present; no date is ever guessed in that case.
    """
    if _POSTED_TODAY_RE.search(line):
        return now.isoformat(), True, ""

    relative = _RELATIVE_POSTED_RE.search(line)
    if relative:
        amount = int(relative.group(1))
        unit = relative.group(2).lower()
        delta = _RELATIVE_UNIT_TO_TIMEDELTA[unit](amount)
        return (now - delta).isoformat(), True, ""

    iso_match = _ISO_DATE_RE.search(line)
    if iso_match:
        try:
            parsed = datetime.fromisoformat(iso_match.group(1)).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
        else:
            return parsed.isoformat(), True, ""

    return None, False, "no_date_on_page"


def _extract_roles(markdown: str, now: datetime) -> list[CareerRoleRecord]:
    """Extract individual role listings (deduped, order-preserving) from markdown."""
    roles: list[CareerRoleRecord] = []
    seen: set[str] = set()
    for line in _ROLE_LINE_RE.findall(markdown):
        title = line.strip()
        if not title or title in seen:
            continue
        seen.add(title)
        posted_at, found, reason = _parse_posted_at(title, now)
        roles.append(
            CareerRoleRecord(
                title=title,
                posted_at=posted_at,
                posted_at_found=found,
                posted_at_reason=reason,
            )
        )
    return roles


def _filter_roles_within_hours(
    roles: list[CareerRoleRecord],
    posted_within_hours: int | None,
    now: datetime,
) -> list[CareerRoleRecord]:
    """Keep roles posted within the window; dateless roles always pass through."""
    if posted_within_hours is None:
        return roles
    cutoff = now - timedelta(hours=posted_within_hours)
    kept: list[CareerRoleRecord] = []
    for role in roles:
        if not role.posted_at_found or role.posted_at is None:
            kept.append(role)  # no fabrication — unknown date is never treated as stale
            continue
        if datetime.fromisoformat(role.posted_at) >= cutoff:
            kept.append(role)
    return kept


async def run_careers(req: RunRequest, crawler: ScoutCrawler) -> list[dict]:
    base = _base_url(req)
    company = _company_name(req)
    slug = re.sub(r"[^a-z0-9]+", "_", company.lower()).strip("_")

    all_markdown = ""
    all_links: list[str] = []
    careers_url = ""
    source = None

    for url in _candidate_urls(base):
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

    now = datetime.now(timezone.utc)
    roles = _extract_roles(all_markdown, now)
    roles = _filter_roles_within_hours(roles, req.posted_within_hours, now)

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
        roles=roles,
        posted_within_hours=req.posted_within_hours,
        source_url=careers_url,
        confidence=0.75 if ats or departments else 0.5,
        citations=[make_citation(source, "careers_url", careers_url, summary[:200])],
    )
    return [record.model_dump(mode="json")]
