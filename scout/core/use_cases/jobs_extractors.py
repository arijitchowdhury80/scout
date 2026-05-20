"""Job posting extraction helpers."""

from __future__ import annotations

import re
from hashlib import sha1

from bs4 import BeautifulSoup

from scout.core.use_cases.jobs import JobPostingRecord
from scout.core.use_cases.jobs_sources import JobSourcePlatform


_SALARY_RANGE_RE = re.compile(
    r"\$?\s*(?P<min>\d{2,3}(?:,\d{3})?)\s*(?:-|–|to)\s*\$?\s*(?P<max>\d{2,3}(?:,\d{3})?)",
    re.IGNORECASE,
)


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _first_text(soup: BeautifulSoup, selectors: list[str]) -> str:
    for selector in selectors:
        found = soup.select_one(selector)
        if found:
            text = _clean(found.get_text(" ", strip=True))
            if text:
                return text
    return ""


def _salary_range(text: str) -> tuple[int | None, int | None]:
    match = _SALARY_RANGE_RE.search(text)
    if not match:
        return None, None
    return int(match.group("min").replace(",", "")), int(match.group("max").replace(",", ""))


def _company_from_greenhouse_url(url: str) -> str:
    match = re.search(r"greenhouse\.io/([^/]+)/jobs", url)
    if not match:
        return ""
    return match.group(1).replace("-", " ").title()


def _object_id(company: str, url: str, apply_url: str = "") -> str:
    match = re.search(r"/jobs/(\d+)", f"{url} {apply_url}")
    slug = re.sub(r"[^a-z0-9]+", "_", company.lower()).strip("_") or "unknown"
    suffix = match.group(1) if match else sha1(url.encode("utf-8")).hexdigest()[:12]
    return f"job_{slug}_{suffix}"


def extract_job_posting_from_html(
    *, html: str, url: str, platform: JobSourcePlatform
) -> JobPostingRecord:
    soup = BeautifulSoup(html, "html.parser")
    title = _first_text(soup, ["h1", "[data-testid='job-title']", ".job-title"])
    company = _first_text(soup, [".company-name", "[data-testid='company-name']"])
    if not company and platform == JobSourcePlatform.GREENHOUSE:
        company = _company_from_greenhouse_url(url)
    location = _first_text(soup, [".location", "[data-testid='location']", ".job-location"])
    content = soup.select_one(".content") or soup.body or soup
    description = _clean(content.get_text(" ", strip=True))
    salary_min, salary_max = _salary_range(description)
    apply_url = ""
    for link in soup.find_all("a", href=True):
        href = str(link.get("href", ""))
        label = _clean(link.get_text(" ", strip=True)).lower()
        if "apply" in label or "#app" in href:
            apply_url = href
            break

    return JobPostingRecord(
        objectID=_object_id(company, url, apply_url),
        company=company,
        title=title,
        url=url,
        location=location,
        salary_min=salary_min,
        salary_max=salary_max,
        description=description,
        apply_url=apply_url,
        ats_platform=platform.value,
        source_platform=platform.value,
        raw_source_url=url,
        source_confidence=0.9 if title and description else 0.4,
    )
