"""Company intelligence runner — scrapes about/team pages for real data."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import structlog
from bs4 import BeautifulSoup, Tag

from scout.core.crawler import ScoutCrawler
from scout.core.enrich.sec import sec_executives
from scout.core.enrich.wikidata import WikidataExec, wikidata_executives
from scout.core.enrich.wikipedia import wikipedia_executives
from scout.core.llm_extract import llm_extract_executives, llm_select_pages
from scout.core.platform.types import Citation, FetchResult, RunRequest
from scout.core.use_cases.prism import CompanyRecord, CompanySocialRecord, ExecutiveRecord
from scout.core.use_cases.runners.base import (
    evidence_from_scrape,
    make_citation,
    safe_scrape,
)

logger = structlog.get_logger(__name__)

# Hard cap on secondary sitemap discovery so a giant sitemap can't hang a scan.
# 10s balances latency against giving normal sitemaps time to return.
_SITEMAP_TIMEOUT_S = 10.0

_ABOUT_PATHS = ["/about", "/about-us", "/company", "/our-story"]
_TEAM_PATHS = [
    "/team",
    "/leadership",
    "/about/team",
    "/about/leadership",
    "/our-team",
    "/company/leadership",
    "/about/management",
    # MOAT Layer 2: broadened guess backstops (used only when link-harvest +
    # sitemap surface no candidate). Real rosters live at many shapes.
    "/company",
    "/company/about",
    "/company/team",
    "/people",
    "/our-people",
    "/who-we-are",
    "/management",
    "/management-team",
    "/meet-the-team",
    "/leadership-team",
    "/about/leadership-team",
]

# MOAT Layer 2 — leadership-page link discovery. The homepage nav/footer is
# where a human deliberately links "Leadership"/"Company"/"Team", so it is the
# highest-signal, lowest-noise source for the ONE page we want — far better than
# the sitemap, which either omits the page (small marketing sites: anthropic.com
# has 12 sitemap URLs, none is /company) or buries it under hundreds of same-
# keyword URLs (datadoghq.com: 213 sitemap matches, almost all press releases).
# Verified live 2026-07-27.
_LEADERSHIP_STRONG = (
    "leadership",
    "leadership-team",
    "our-team",
    "meet-the-team",
    "management-team",
    "our-people",
    "executive",
    "executives",
    "board-of-directors",
    "our-leadership",
)
_LEADERSHIP_MEDIUM = (
    "team",
    "people",
    "management",
    "who-we-are",
    "company",
    "about",
    "our-story",
    "mission",
    "board",
    "leaders",
)
# Segments that look leadership-ish by keyword but are noise for THIS page —
# de-noises the sitemap (datadoghq.com press releases) and drops auth/utility.
_DISCOVERY_EXCLUDE = (
    "news",
    "press",
    "press-release",
    "press-releases",
    "latest-news",
    "blog",
    "careers",
    "career",
    "jobs",
    "changelog",
    "category",
    "login",
    "signin",
    "sign-in",
    "register",
    "signup",
    "dashboard",
    "account",
    "cart",
    "checkout",
    "privacy",
    "terms",
    "cookie",
    "status",
    "support",
    "docs",
    "documentation",
    "pricing",
    "download",
    "search",
    "legal",
    "security",
    "academy",
    "help",
    "contact",
    "events",
    "webinars",
    "resources",
    "customers",
    "partners",
    "investors",
)
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


def _fallback_llm_api_key(crawler: ScoutCrawler) -> str:
    """Effective LLM-fallback key for this crawler, defensively typed.

    `crawler` is a real `ScoutCrawler` in production, but unit tests pass a
    `MagicMock()` — accessing an unset attribute on a Mock returns another
    Mock (truthy, not a str), which would otherwise look like "an API key is
    configured" and trigger a real LLM call from every existing test that
    doesn't set it. Guard the type so only an actual configured string ever
    counts as a key.
    """
    key = getattr(crawler, "fallback_llm_api_key", "")
    return key if isinstance(key, str) else ""


def _enrichment_on(crawler: ScoutCrawler) -> bool:
    """Whether external exec enrichment is enabled for this crawler.

    Defensively typed like `_fallback_llm_api_key`: unit tests pass a
    `MagicMock()` whose unset attribute is a truthy Mock, which must NOT be read
    as 'enrichment on' (that would fire a live Wikidata HTTP call from every
    mock-crawler test). Only a real bool True counts.
    """
    return getattr(crawler, "enrichment_enabled", False) is True


def _make_wikidata_exec_record(company: str, wexec: WikidataExec) -> ExecutiveRecord:
    """Map a Wikidata leader onto an ExecutiveRecord with Wikidata provenance."""
    slug = re.sub(r"[^a-z0-9]+", "_", wexec.name.lower()).strip("_")
    entity_url = f"https://www.wikidata.org/wiki/{wexec.company_qid}" if wexec.company_qid else ""
    person_url = f"https://www.wikidata.org/wiki/{wexec.qid}" if wexec.qid else ""
    return ExecutiveRecord(
        objectID=f"exec_{slug}",
        company=company,
        name=wexec.name,
        title=wexec.title,
        profile_url=person_url,
        source_url=entity_url,
        confidence=0.7,
        citations=[
            Citation(
                source_id=wexec.company_qid or "wikidata",
                source_url=entity_url,
                field="name",
                claim=wexec.name,
                snippet=f"{wexec.name} — {wexec.title} (Wikidata)".strip(" —"),
                confidence=0.7,
            )
        ],
    )


def _make_sec_exec_record(company: str, name: str, title: str) -> ExecutiveRecord:
    """Map an SEC EDGAR officer/director onto an ExecutiveRecord with provenance."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    src = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
    return ExecutiveRecord(
        objectID=f"exec_{slug}",
        company=company,
        name=name,
        title=title,
        source_url=src,
        confidence=0.8,  # authoritative structured filing
        citations=[
            Citation(
                source_id="sec_edgar",
                source_url=src,
                field="name",
                claim=name,
                snippet=f"{name} — {title} (SEC Form 3/4)".strip(" —"),
                confidence=0.8,
            )
        ],
    )


def _make_wikipedia_exec_record(company: str, name: str, title: str) -> ExecutiveRecord:
    """Map a Wikipedia-sourced leader onto an ExecutiveRecord with provenance."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    article = "https://en.wikipedia.org/wiki/" + company.replace(" ", "_")
    return ExecutiveRecord(
        objectID=f"exec_{slug}",
        company=company,
        name=name,
        title=title,
        source_url=article,
        confidence=0.65,
        citations=[
            Citation(
                source_id="wikipedia",
                source_url=article,
                field="name",
                claim=name,
                snippet=f"{name} — {title} (Wikipedia)".strip(" —"),
                confidence=0.65,
            )
        ],
    )


async def _extract_executives_via_llm(
    company: str, source: FetchResult, api_key: str, *, content: str = ""
) -> list[ExecutiveRecord]:
    """LLM adjudication for executives — called when the structured heuristics
    (JSON-LD Person nodes, team cards) found zero executives for this run, in
    place of the noisy regex. Company-identity guarded (only THIS company's
    leaders). Never fabricates: any item the model returns that doesn't parse
    into a real name is dropped.

    `content` overrides which text the model adjudicates. Callers pass the
    combined rendered markdown of every page fetched (team/leadership page
    first, then about/homepage) so the model sees the roster wherever it
    actually lives — a guessed /team path often 200s without listing anyone,
    while the real leaders sit on the homepage or an unguessed page (the Stripe
    repro: /team had 0, the CEO was on the homepage). Defaults to the single
    source's markdown for backward compatibility.
    """
    items = await llm_extract_executives(
        content or source.markdown,
        api_key,
        page_url=source.evidence.source_url,
        company=company,
    )
    records: list[ExecutiveRecord] = []
    for item in items:
        name = item.name.strip()
        if not name:
            continue
        records.append(
            _make_exec_record(
                company,
                name,
                item.title.strip(),
                source,
                snippet=f"{name} — {item.title}".strip(" —"),
                confidence=0.6,
            )
        )
    logger.info(
        "[scout/company] llm executive fallback fired",
        company=company,
        url=source.evidence.source_url,
        records_found=len(records),
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


def _url_is_excluded(url: str) -> bool:
    """True when a path segment marks the URL as leadership-noise (press/blog/
    careers/login/...) — de-noises the sitemap and blocks a strong anchor text
    from rescuing a genuine blog/press URL."""
    return any(seg in _DISCOVERY_EXCLUDE for seg in urlparse(url).path.lower().split("/") if seg)


def _leadership_score(url: str) -> int:
    """Score a URL PATH as a leadership-page candidate. 0 = reject.

    Strong path segment (leadership/our-team/...) = 3; medium (company/about/
    team/...) = 1; any excluded segment (press/blog/careers/login/...) = 0 even
    if it also matched a keyword — this is what de-noises a sitemap that buries
    the real /leadership under press releases.
    """
    segments = [s for s in urlparse(url).path.lower().split("/") if s]
    if not segments or _url_is_excluded(url):
        return 0
    if any(seg in _LEADERSHIP_STRONG for seg in segments):
        return 3
    if any(seg in _LEADERSHIP_MEDIUM for seg in segments):
        return 1
    return 0


def _leadership_text_score(text: str) -> int:
    """Score a link's VISIBLE ANCHOR TEXT as a leadership signal. Often more
    reliable than the URL slug: a site may link "Our People" or "Meet the team"
    to a cryptic URL the path-scorer would miss. This is the cheap, DOM-native
    version of "read the nav" — no vision/screenshot needed, since the rendered
    HTML already carries the anchor text.
    """
    joined = re.sub(r"[^a-z]+", "-", text.lower()).strip("-")
    if not joined:
        return 0
    words = set(joined.split("-"))
    if any(kw in joined for kw in _LEADERSHIP_STRONG) or (words & set(_LEADERSHIP_STRONG)):
        return 3
    if words & set(_LEADERSHIP_MEDIUM):
        return 1
    return 0


def _discover_leadership_urls(
    base: str, candidates: list[str | tuple[str, str]], limit: int = 3
) -> list[str]:
    """Rank candidates for the real leadership/team page. Each candidate is a
    URL, or a (url, anchor_text) pair — anchor text is scored alongside the URL
    path (whichever is stronger wins), so a nav link that SAYS "Leadership" but
    points to a keyword-less URL still ranks. Same-host only; excludes the
    homepage; strongest signal + shallowest path first. Pass nav candidates
    before sitemap ones so a human-curated nav link wins ties (stable order).
    """
    base_host = urlparse(base).netloc.lower().removeprefix("www.")
    base_norm = base.rstrip("/")
    scored: list[tuple[int, int, int, str]] = []
    seen: set[str] = set()
    for order, candidate in enumerate(candidates):
        url, text = candidate if isinstance(candidate, tuple) else (candidate, "")
        if not url or not url.startswith(("http://", "https://")):
            continue
        norm = url.rstrip("/")
        if norm == base_norm or norm in seen:
            continue
        host = urlparse(url).netloc.lower().removeprefix("www.")
        if host != base_host:
            continue
        # An excluded URL (blog/press/careers) is never a roster page, no matter
        # what its link text claims.
        if _url_is_excluded(url):
            continue
        score = max(_leadership_score(url), _leadership_text_score(text))
        if score <= 0:
            continue
        seen.add(norm)
        depth = len([s for s in urlparse(url).path.split("/") if s])
        # sort key: higher score, shallower path, earlier input order (nav-first)
        scored.append((-score, depth, order, norm))
    scored.sort()
    return [url for _, _, _, url in scored[:limit]]


def _prefilter_candidates(
    base: str,
    anchors: list[tuple[str, str]],
    sitemap_urls: list[str],
    limit: int = 60,
) -> list[tuple[str, str]]:
    """Rank + bound (anchor_text, url) candidates to hand the LLM page-selector.

    `anchors` are (url, anchor_text) pairs from `_extract_anchor_candidates`;
    sitemap URLs carry no text. Returns (anchor_text, url) pairs — the shape
    `llm_select_pages` expects — with leadership-signalled candidates FIRST so
    the real team/leadership link survives the cap instead of being crowded out
    by sitemap noise (the Figma repro: 300 sitemap color-swatch pages buried the
    about link). Same-host, non-excluded, de-duped.
    """
    base_host = urlparse(base).netloc.lower().removeprefix("www.")
    base_norm = base.rstrip("/")
    scored: list[tuple[int, int, str, str]] = []
    seen: set[str] = set()
    # anchors are (url, text); sitemap urls have no anchor text.
    for order, (url, text) in enumerate([*anchors, *[(u, "") for u in sitemap_urls]]):
        if not url or not url.startswith(("http://", "https://")):
            continue
        norm = url.rstrip("/")
        if norm == base_norm or norm in seen:
            continue
        if urlparse(url).netloc.lower().removeprefix("www.") != base_host:
            continue
        if _url_is_excluded(url):
            continue
        seen.add(norm)
        signal = max(_leadership_score(url), _leadership_text_score(text))
        # higher signal first, then original order (nav before sitemap)
        scored.append((-signal, order, text, url))
    scored.sort()
    return [(text, url) for _, _, text, url in scored[:limit]]


def _extract_anchor_candidates(html: str, base: str) -> list[tuple[str, str]]:
    """Harvest (absolute_url, anchor_text) pairs from a page's <a> tags. This is
    the nav/footer link list a human reads to find "Leadership" — captured from
    the rendered DOM, which is strictly richer and cheaper than a screenshot."""
    if not html:
        return []
    pairs: list[tuple[str, str]] = []
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        if not isinstance(a, Tag):
            continue
        href = a.get("href")
        if not isinstance(href, str) or not href.strip():
            continue
        text = re.sub(r"\s+", " ", a.get_text() or "").strip()
        pairs.append((urljoin(base + "/", href.strip()), text))
    return pairs


async def _sitemap_urls(crawler: ScoutCrawler, base: str, *, max_pages: int = 300) -> list[str]:
    """Best-effort sitemap/URL discovery for leadership-page hunting.

    Routed through the injected `crawler.map_urls` (NOT the module-level
    map_urls) so it honours the DI boundary and unit tests with a mock crawler
    never hit the network. Tolerant: any failure — including a mock whose
    map_urls isn't awaitable — returns [] so the runner falls back to
    link-harvest + guessed paths.
    """
    try:
        from scout.core.types import MapRequest

        # PRODUCTION robustness: a huge sitemap index (e.g. adobe.com,
        # datadoghq.com's 14-way index → thousands of URLs) must NEVER hang a
        # company scan. Bound the discovery hard; on timeout, fall back to
        # nav-link harvest + guessed paths. Sitemap is the SECONDARY source
        # here, so losing it degrades gracefully.
        resp = await asyncio.wait_for(
            crawler.map_urls(MapRequest(url=base, max_pages=max_pages)),
            timeout=_SITEMAP_TIMEOUT_S,
        )
        return resp.urls if resp.success else []
    except (Exception, asyncio.TimeoutError) as exc:  # noqa: BLE001 - best-effort
        logger.info("[scout/company] sitemap discovery skipped", base=base, error=str(exc))
        return []


async def run_company(req: RunRequest, crawler: ScoutCrawler) -> list[dict]:
    base = _base_url(req)
    company = _company_name(req)
    slug = re.sub(r"[^a-z0-9]+", "_", company.lower()).strip("_")

    all_markdown = ""
    all_links: list[str] = []
    sources: list[FetchResult] = []

    # The homepage is the PRIMARY discovery source (nav + FOOTER links, where the
    # "Leadership"/"Team"/"About" link usually lives) — so it gets the full
    # intelligence render: footer links often only appear after scan_full_page
    # scrolls the page (measured: a light render here regressed coverage on
    # Cloudflare/Patagonia, whose leadership link is footer-only). Latency is
    # trimmed on the SECONDARY fetches instead (about page = light, ≤2 candidate
    # pages, shorter sitemap cap).
    homepage = await safe_scrape(crawler, base, intelligence_render=True)
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

    async def scrape_first(
        paths: list[str], *, require_signal: bool = False, intelligence_render: bool = True
    ) -> None:
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
            resp = await safe_scrape(crawler, url, intelligence_render=intelligence_render)
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

    # About page: fetched for a description + more nav links → light render.
    await scrape_first(_ABOUT_PATHS, intelligence_render=False)

    # MOAT Layer 2 — reach the REAL leadership page instead of only guessing.
    # Primary source: links harvested from the rendered homepage/about nav+footer
    # (where humans link "Leadership"/"Company"/"Team"). Secondary: the sitemap,
    # hard-ranked and de-noised (it either omits the page or buries it). Fetch
    # the top candidates and adopt ALL of them — the LLM adjudicator (company-
    # identity guarded) reads every fetched page, so extra right pages lift
    # recall without hurting precision. Guessed _TEAM_PATHS remain a backstop
    # only when link-harvest + sitemap surface nothing.
    sitemap = await _sitemap_urls(crawler, base)
    anchors: list[tuple[str, str]] = []
    for src in sources:  # homepage + about fetched so far — richest nav coverage
        anchors.extend(_extract_anchor_candidates(src.html, base))

    # Production-general page selection: when a key is available, let the LLM
    # pick the leadership page from the site's ACTUAL link inventory (anchor
    # text + URL), language- and structure-agnostic — no hardcoded path/keyword
    # list. The deterministic keyword ranker (_discover_leadership_urls) is the
    # offline/no-key fallback, and also catches the case where the LLM selector
    # returns nothing.
    llm_key = _fallback_llm_api_key(crawler)
    leadership_urls: list[str] = []
    if llm_key:
        select_candidates = _prefilter_candidates(base, anchors, sitemap)
        if select_candidates:
            # LATENCY: cap at 2 — each selected page gets a full intelligence
            # render (~8s). The LLM selector returns most-likely-first, so 2
            # covers the common "roster + overview" split (GitLab e-group +
            # /company) without a third expensive fetch.
            leadership_urls = await llm_select_pages(
                company, select_candidates, llm_key, target="leadership", limit=2
            )
    if not leadership_urls:
        leadership_urls = _discover_leadership_urls(base, [*anchors, *sitemap], limit=2)
    adopted_candidate = False
    for url in leadership_urls:
        resp = await safe_scrape(crawler, url, intelligence_render=True)
        if resp:
            _adopt(evidence_from_scrape(url, resp))
            adopted_candidate = True
    if not adopted_candidate:
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
        # MOAT (Layer 3): JSON-LD Person nodes + team cards (both structured
        # and reasonably precise) found nothing. Prefer LLM adjudication over
        # the noisy regex-over-concatenated-markdown path — the gauntlet proved
        # that regex is the dominant garbage source, returning OTHER companies'
        # CEOs (Stripe -> Lightspeed, Datadog -> MongoDB) and article authors,
        # because it matched any "Name, Title" string anywhere across the
        # homepage+about+team markdown. The LLM adjudicator is company-identity
        # guarded (see llm_extract._EXECUTIVE_COMPANY_GUARD). GATE 1 proved the
        # exec content is present in the intelligence-rendered pages, so the
        # adjudicator has the raw material it needs. The regex survives only as
        # the no-LLM-key legacy path.
        llm_api_key = _fallback_llm_api_key(crawler)
        if llm_api_key:
            # Adjudicate over ALL fetched pages, most-specific first: the
            # team/leadership page leads (so it survives the model's content
            # cap), followed by about + homepage, where the roster often
            # actually lives when a guessed /team path 200s but lists no one.
            combined = "\n\n".join(src.markdown for src in reversed(sources) if src.markdown)
            executives = await _extract_executives_via_llm(
                company, sources[-1], llm_api_key, content=combined
            )
        else:
            executives = _extract_executives(all_markdown, company, primary)

    # WATERFALL source #2 — Wikidata enrichment. ~half of companies never
    # publish leadership on their own site (Stripe, Vercel, most retail brands),
    # so on-site alone caps coverage at ~50%. Wikidata (free, structured,
    # domain-disambiguated) fills the gap AND adds founders/board the site omits.
    # On-site records win on a name clash (freshest, most detailed); Wikidata
    # only ADDS names not already present.
    if _enrichment_on(crawler):
        domain = urlparse(base).netloc
        for wexec in await wikidata_executives(company, domain):
            key = wexec.name.lower().strip()
            if key and key not in seen_names:
                seen_names.add(key)
                executives.append(_make_wikidata_exec_record(company, wexec))

        # WATERFALL source #3 — SEC EDGAR (US public companies). Authoritative,
        # structured officer/director data; no LLM, can't hallucinate a title.
        # ADDS names not already present (on-site/Wikidata win on a clash).
        for sexec in await sec_executives(company):
            key = sexec.name.lower().strip()
            if key and key not in seen_names:
                seen_names.add(key)
                executives.append(_make_sec_exec_record(company, sexec.name, sexec.title))

        # WATERFALL source #4 — Wikipedia article extraction. Fires ONLY when the
        # company is still uncovered after on-site + Wikidata (bounds the LLM
        # cost to the gaps). Wikidata's structured claims are thin for many
        # notable private firms (Notion has an entity but no CEO claim) — their
        # Wikipedia prose names the founders/CEO. Reuses the domain-disambiguated
        # entity + the company-guarded extractor. Grounded + keyless.
        wiki_key = _fallback_llm_api_key(crawler)
        if not executives and wiki_key:
            for witem in await wikipedia_executives(company, domain, wiki_key):
                name = witem.name.strip()
                key = name.lower()
                if name and key not in seen_names:
                    seen_names.add(key)
                    executives.append(
                        _make_wikipedia_exec_record(company, name, witem.title.strip())
                    )

    for exec_rec in executives:
        records.append(exec_rec.model_dump(mode="json"))

    socials = _extract_socials(all_markdown, all_links, company, primary)
    for social_rec in socials:
        records.append(social_rec.model_dump(mode="json"))

    return records
