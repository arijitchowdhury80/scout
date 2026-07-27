"""Company intelligence runner — scrapes about/team pages for real data."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from scout.core.crawler import ScoutCrawler
from scout.core.platform.types import FetchResult, RunRequest
from scout.core.use_cases.prism import CompanyRecord, CompanySocialRecord, ExecutiveRecord
from scout.core.use_cases.runners.base import (
    evidence_from_scrape,
    make_citation,
    safe_scrape,
)

_ABOUT_PATHS = ["/about", "/about-us", "/company", "/our-story"]
_TEAM_PATHS = [
    "/team",
    "/leadership",
    "/about/team",
    "/about/leadership",
    "/our-team",
    "/company/leadership",
    "/about/management",
]
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


_PERSON_NAME_RE = re.compile(r"^[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){1,3}$")
_TEAM_CARD_CLASS_RE = re.compile(
    r"team|staff|leadership|people|person|profile|member|bio|exec", re.I
)
_NAME_CLASS_RE = re.compile(r"name", re.I)
# FX: real leadership pages (e.g. algolia.com/about/leadership) label the title
# element with a "function" class rather than title/role/position/job — added
# here after inspecting the live page (see company.py BUILD-2 investigation).
_TITLE_CLASS_RE = re.compile(r"title|role|position|job|function", re.I)


def _make_exec_record(
    company: str,
    name: str,
    title: str,
    source: FetchResult,
    profile_url: str = "",
    snippet: str = "",
    confidence: float = 0.75,
) -> ExecutiveRecord:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return ExecutiveRecord(
        objectID=f"exec_{slug}",
        company=company,
        name=name,
        title=title,
        profile_url=profile_url,
        source_url=source.evidence.source_url,
        confidence=confidence,
        citations=[
            make_citation(source, "name", name, snippet[:200] or f"{name} — {title}", confidence)
        ],
    )


def _flatten_jsonld(data: Any) -> list[dict[str, Any]]:
    """Flatten a JSON-LD payload into a list of plain dict nodes."""
    nodes: list[dict[str, Any]] = []
    if isinstance(data, list):
        for item in data:
            nodes.extend(_flatten_jsonld(item))
        return nodes
    if not isinstance(data, dict):
        return nodes
    nodes.append(data)
    for key in ("@graph", "employee", "employees", "member", "members", "founder", "founders"):
        val = data.get(key)
        if val:
            nodes.extend(_flatten_jsonld(val))
    return nodes


def _extract_jsonld_people(html: str, company: str, source: FetchResult) -> list[ExecutiveRecord]:
    """Extract executives from schema.org JSON-LD Person nodes."""
    if not html:
        return []
    records: list[ExecutiveRecord] = []
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text() or ""
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            continue
        for node in _flatten_jsonld(data):
            if node.get("@type") != "Person":
                continue
            name = str(node.get("name") or "").strip()
            title = str(node.get("jobTitle") or "").strip()
            if not name or not title:
                continue
            profile_url = str(node.get("url") or "")
            records.append(
                _make_exec_record(
                    company,
                    name,
                    title,
                    source,
                    profile_url=profile_url,
                    snippet=json.dumps(node)[:200],
                    confidence=0.85,
                )
            )
    return records


def _extract_name_text(card: Tag) -> str:
    """Return the person's full name from a team/leadership card.

    Some sites (e.g. algolia.com/about/leadership) split a name across
    sibling elements, e.g. `<span class="people-firstName">Stephen</span>
    <span class="people-lastName"> Lynch</span>`, rather than one element
    holding the whole name. `find(class_=_NAME_CLASS_RE)` alone would only
    ever return the first such span ("Stephen"), which then fails the
    person-name shape check downstream. Concatenate every matching element
    instead so multi-span names come through whole, while single-element
    names (the common case, e.g. `<h3 class="member-name">Jane
    Whitfield</h3>`) still work unchanged.
    """
    itemprop_name = card.find(attrs={"itemprop": "name"})
    if isinstance(itemprop_name, Tag):
        text = itemprop_name.get_text(strip=True)
        if text:
            return text
    name_parts = [el for el in card.find_all(class_=_NAME_CLASS_RE) if isinstance(el, Tag)]
    if name_parts:
        text = re.sub(r"\s+", " ", "".join(el.get_text() for el in name_parts)).strip()
        if text:
            return text
    heading = card.find(["h1", "h2", "h3", "h4", "h5"])
    if isinstance(heading, Tag):
        return heading.get_text(strip=True)
    return ""


def _extract_team_cards(html: str, company: str, source: FetchResult) -> list[ExecutiveRecord]:
    """Extract executives from common team-member card markup (name + title pairs)."""
    if not html:
        return []
    records: list[ExecutiveRecord] = []
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    candidates = soup.find_all(
        ["div", "li", "article", "section", "figure"], class_=_TEAM_CARD_CLASS_RE
    )
    for card in candidates:
        if not isinstance(card, Tag):
            continue
        name = _extract_name_text(card)
        title_el = card.find(attrs={"itemprop": "jobTitle"}) or card.find(class_=_TITLE_CLASS_RE)
        if not name or not title_el:
            continue
        title = title_el.get_text(strip=True)
        if not name or not title or not _PERSON_NAME_RE.match(name) or len(title) > 100:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        profile_url = ""
        link = card.find("a", href=True)
        if isinstance(link, Tag):
            href = link.get("href")
            if isinstance(href, str):
                profile_url = urljoin(source.evidence.source_url, href)
        records.append(
            _make_exec_record(
                company,
                name,
                title,
                source,
                profile_url=profile_url,
                snippet=f"{name} — {title}",
                confidence=0.75,
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


def _has_executive_signal(company: str, source: FetchResult) -> bool:
    """Whether a fetched page actually contains extractable executive data.

    Used to tell a real leadership/team page apart from an unrelated page
    that happens to return success=True for a guessed team path (e.g. a
    login redirect at /team on a site whose real roster lives at
    /about/leadership).
    """
    if _extract_jsonld_people(source.html, company, source):
        return True
    if _extract_team_cards(source.html, company, source):
        return True
    if _extract_executives(source.markdown, company, source):
        return True
    return False


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

    def _adopt(src: FetchResult) -> None:
        nonlocal all_markdown, all_links
        sources.append(src)
        all_markdown += src.markdown + "\n"
        all_links.extend(src.links)

    async def scrape_first(paths: list[str], *, require_signal: bool = False) -> None:
        """Fetch candidate paths in order, keeping the first usable page.

        FX (BUILD-2): a path can return success=True with real markdown that
        isn't actually a team/leadership page — e.g. algolia.com/team
        redirects to a login prompt, not the exec roster at
        algolia.com/about/leadership. Stopping at the first *successful*
        fetch (the old behaviour) locked the runner onto that dead end and
        never reached the real page. When `require_signal` is set, keep
        trying subsequent candidate paths until one actually contains
        executive data; fall back to the first successful fetch only if none
        of the candidates do (so callers still get *a* source instead of
        nothing).
        """
        fallback: FetchResult | None = None
        for path in paths:
            url = urljoin(base + "/", path.lstrip("/"))
            resp = await safe_scrape(crawler, url)
            if not resp:
                continue
            src = evidence_from_scrape(url, resp)
            if not require_signal or _has_executive_signal(company, src):
                _adopt(src)
                return
            if fallback is None:
                fallback = src
        if fallback is not None:
            _adopt(fallback)

    await scrape_first(_ABOUT_PATHS)
    await scrape_first(_TEAM_PATHS, require_signal=True)

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

    executives: list[ExecutiveRecord] = []
    seen_names: set[str] = set()
    for src in sources:
        for exec_rec in _extract_jsonld_people(src.html, company, src):
            key = exec_rec.name.lower()
            if key not in seen_names:
                seen_names.add(key)
                executives.append(exec_rec)
    for src in sources:
        for exec_rec in _extract_team_cards(src.html, company, src):
            key = exec_rec.name.lower()
            if key not in seen_names:
                seen_names.add(key)
                executives.append(exec_rec)
    if not executives:
        executives = _extract_executives(all_markdown, company, primary)
    for exec_rec in executives:
        records.append(exec_rec.model_dump(mode="json"))

    socials = _extract_socials(all_markdown, all_links, company, primary)
    for social_rec in socials:
        records.append(social_rec.model_dump(mode="json"))

    return records
