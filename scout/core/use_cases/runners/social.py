"""Social runner — scrapes public social profiles for company signals."""

from __future__ import annotations

import re

from scout.core.crawler import ScoutCrawler
from scout.core.platform.types import RunRequest
from scout.core.use_cases.prism import CompanySocialRecord
from scout.core.use_cases.runners.base import (
    evidence_from_scrape,
    make_citation,
    safe_scrape,
)

_FOLLOWER_PATTERNS = [
    re.compile(r"([\d,]+\.?\d*[KMkm]?)\s*(?:followers|Followers)", re.I),
    re.compile(r"(?:followers|Followers)[:\s]+([\d,]+\.?\d*[KMkm]?)", re.I),
]

_BIO_PATTERNS = [
    re.compile(r"(?:Bio|About|Description)[:\s]+(.+?)(?:\n|$)", re.I),
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


def _extract_follower_count(markdown: str) -> str:
    for pattern in _FOLLOWER_PATTERNS:
        match = pattern.search(markdown)
        if match:
            return match.group(1).strip()
    return ""


def _extract_bio(markdown: str) -> str:
    for pattern in _BIO_PATTERNS:
        match = pattern.search(markdown)
        if match:
            return match.group(1).strip()[:300]
    lines = [ln.strip() for ln in markdown.split("\n") if ln.strip() and not ln.startswith("#")]
    return lines[0][:300] if lines else ""


async def run_social(req: RunRequest, crawler: ScoutCrawler) -> list[dict]:
    base = _base_url(req)
    company = _company_name(req)
    slug = re.sub(r"[^a-z0-9]+", "_", company.lower()).strip("_")

    records: list[dict] = []

    homepage = await safe_scrape(crawler, base, use_js=False)
    social_urls: dict[str, str] = {}
    if homepage:
        text = homepage.markdown + "\n" + "\n".join(homepage.links)
        patterns = {
            "linkedin": re.compile(r"https?://(?:www\.)?linkedin\.com/company/[^\s\"')]+"),
            "twitter": re.compile(r"https?://(?:www\.)?(?:twitter|x)\.com/[^\s\"')]+"),
            "facebook": re.compile(r"https?://(?:www\.)?facebook\.com/[^\s\"')]+"),
            "instagram": re.compile(r"https?://(?:www\.)?instagram\.com/[^\s\"')]+"),
            "youtube": re.compile(r"https?://(?:www\.)?youtube\.com/(?:c/|channel/|@)[^\s\"')]+"),
        }
        for platform, pattern in patterns.items():
            match = pattern.search(text)
            if match:
                social_urls[platform] = match.group(0).rstrip(")")

    for url in req.targets:
        lower = url.lower()
        for platform in ["linkedin", "twitter", "facebook", "instagram", "youtube"]:
            if platform in lower or (platform == "twitter" and "x.com" in lower):
                social_urls[platform] = url
                break

    for platform, url in social_urls.items():
        resp = await safe_scrape(crawler, url, use_js=False)
        if resp:
            source = evidence_from_scrape(url, resp)
            bio = _extract_bio(resp.markdown)

            handle = ""
            handle_match = re.search(r"@([\w.-]+)", resp.markdown)
            if handle_match:
                handle = handle_match.group(0)

            records.append(
                CompanySocialRecord(
                    objectID=f"social_{slug}_{platform}",
                    company=company,
                    platform=platform,
                    url=url,
                    handle=handle,
                    provider="crawl4ai",
                    confidence=0.6,
                    citations=[make_citation(source, "url", url, bio[:200] or url)],
                ).model_dump(mode="json")
            )
        else:
            records.append(
                CompanySocialRecord(
                    objectID=f"social_{slug}_{platform}",
                    company=company,
                    platform=platform,
                    url=url,
                    provider="crawl4ai",
                    confidence=0.3,
                ).model_dump(mode="json")
            )

    return records
