"""Company intelligence runner — scrapes about/team pages for real data."""

from __future__ import annotations

import re
from urllib.parse import urljoin

from scout.core.crawler import ScoutCrawler
from scout.core.platform.types import FetchResult, RunRequest
from scout.core.use_cases.prism import CompanyRecord, CompanySocialRecord, ExecutiveRecord
from scout.core.use_cases.runners.base import (
    evidence_from_scrape,
    make_citation,
    safe_scrape,
)

_ABOUT_PATHS = ["/about", "/about-us", "/company", "/our-story"]
_TEAM_PATHS = ["/team", "/leadership", "/about/team", "/about/leadership"]
_SOCIAL_PATTERNS = {
    "linkedin": re.compile(r"https?://(?:www\.)?linkedin\.com/company/[^\s\"')]+"),
    "twitter": re.compile(r"https?://(?:www\.)?(?:twitter|x)\.com/[^\s\"')]+"),
    "facebook": re.compile(r"https?://(?:www\.)?facebook\.com/[^\s\"')]+"),
}


def _base_url(req: RunRequest) -> str:
    if req.url:
        return req.url.rstrip("/")
    if req.targets:
        return req.targets[0].rstrip("/")
    name = req.query.strip().lower().replace(" ", "")
    return f"https://www.{name}.com"


def _company_name(req: RunRequest) -> str:
    return req.query.strip() or (req.targets[0] if req.targets else "unknown")


def _extract_description(markdown: str, limit: int = 500) -> str:
    lines = [ln.strip() for ln in markdown.split("\n") if ln.strip() and not ln.startswith("#")]
    text = " ".join(lines)
    return text[:limit].strip()


def _extract_executives(markdown: str, company: str, source: FetchResult) -> list[ExecutiveRecord]:
    records: list[ExecutiveRecord] = []
    patterns = [
        re.compile(
            r"(?:^|\n)\s*\*?\*?([A-Z][a-z]+ (?:[A-Z][a-z]+ )?[A-Z][a-z]+)\*?\*?"
            r"[\s,–—-]+\*?\*?([A-Za-z &/,]+(?:Officer|Director|President|VP|"
            r"Manager|Head|Lead|Chief|Founder|CEO|CTO|CFO|COO|CMO|CRO|CIO|CPO)[A-Za-z &/,]*)\*?\*?",
        ),
        re.compile(
            r"\*\*([A-Z][a-z]+ (?:[A-Z][a-z]+ )?[A-Z][a-z]+)\*\*[^A-Z]*?"
            r"((?:Chief|VP|Head|Director|President|Founder|CEO|CTO|CFO|COO|CMO|CRO)"
            r"[A-Za-z &/,]*)",
        ),
    ]
    seen_names: set[str] = set()
    for pattern in patterns:
        for match in pattern.finditer(markdown):
            name = match.group(1).strip()
            title = match.group(2).strip().rstrip(",. ")
            if name in seen_names or len(name) > 60 or len(title) > 100:
                continue
            seen_names.add(name)
            slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
            records.append(
                ExecutiveRecord(
                    objectID=f"exec_{slug}",
                    company=company,
                    name=name,
                    title=title,
                    source_url=source.evidence.source_url,
                    confidence=0.7,
                    citations=[make_citation(source, "name", name, match.group(0).strip()[:200])],
                )
            )
    return records


def _extract_socials(
    markdown: str, links: list[str], company: str, source: FetchResult
) -> list[CompanySocialRecord]:
    records: list[CompanySocialRecord] = []
    all_text = markdown + "\n" + "\n".join(links)
    for platform, pattern in _SOCIAL_PATTERNS.items():
        match = pattern.search(all_text)
        if match:
            url = match.group(0).rstrip(")")
            slug = re.sub(r"[^a-z0-9]+", "_", company.lower()).strip("_")
            records.append(
                CompanySocialRecord(
                    objectID=f"social_{slug}_{platform}",
                    company=company,
                    platform=platform,
                    url=url,
                    provider="crawl4ai",
                    confidence=0.8,
                    citations=[make_citation(source, "url", url, url[:200])],
                )
            )
    return records


async def run_company(req: RunRequest, crawler: ScoutCrawler) -> list[dict]:
    base = _base_url(req)
    company = _company_name(req)
    slug = re.sub(r"[^a-z0-9]+", "_", company.lower()).strip("_")

    all_markdown = ""
    all_links: list[str] = []
    sources: list[FetchResult] = []

    homepage = await safe_scrape(crawler, base)
    if homepage:
        src = evidence_from_scrape(base, homepage)
        sources.append(src)
        all_markdown += homepage.markdown + "\n"
        all_links.extend(homepage.links)

    async def scrape_first(paths: list[str]) -> None:
        nonlocal all_markdown, all_links
        for path in paths:
            url = urljoin(base + "/", path.lstrip("/"))
            resp = await safe_scrape(crawler, url)
            if not resp:
                continue
            src = evidence_from_scrape(url, resp)
            sources.append(src)
            all_markdown += resp.markdown + "\n"
            all_links.extend(resp.links)
            return

    await scrape_first(_ABOUT_PATHS)
    await scrape_first(_TEAM_PATHS)

    if not sources:
        return []

    primary = sources[0]
    description = _extract_description(all_markdown)
    source_urls = list({s.evidence.source_url for s in sources})

    records: list[dict] = []

    company_rec = CompanyRecord(
        objectID=f"company_{slug}",
        name=company,
        website=base,
        description=description,
        source_urls=source_urls,
        confidence=0.8 if description else 0.5,
        citations=[make_citation(primary, "description", description[:100], description[:200])],
    )
    records.append(company_rec.model_dump(mode="json"))

    executives = _extract_executives(all_markdown, company, primary)
    for exec_rec in executives:
        records.append(exec_rec.model_dump(mode="json"))

    socials = _extract_socials(all_markdown, all_links, company, primary)
    for social_rec in socials:
        records.append(social_rec.model_dump(mode="json"))

    return records
