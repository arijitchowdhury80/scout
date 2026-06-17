"""crawl-from-here — turn a cleared session into structured detail records.

Once a human has cleared a site's challenge (see `human_assisted`), Scout has a
live, authenticated browser. This module discovers detail-page links on the
cleared page and visits each *in that same session* (so the anti-bot cookie
carries and they don't re-challenge), extracting clean markdown + any JSON-LD.

Engine-pure: depends only on `scout.core.blocking`. The browser is injected as a
`NavigateBridge`, and sleep is injected, so the flow is fully unit-testable.
"""

from __future__ import annotations

import json
import re
from typing import Awaitable, Callable, Protocol
from urllib.parse import urljoin, urlparse

from pydantic import BaseModel

from scout.core.blocking import detect_block
from scout.core.human_assisted import CaptureLike

_HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
_JSONLD_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
_SKIP_PREFIXES = ("mailto:", "tel:", "javascript:", "#")


def extract_detail_links(
    html: str, base_url: str, *, contains: str = "", limit: int = 5
) -> list[str]:
    """Discover same-domain detail links on a page, resolved to absolute URLs.

    Drops off-site links, mailto/tel/js/fragment junk, and (when `contains` is
    given) anything whose URL lacks that substring. Dedupes preserving order;
    caps at `limit`.
    """
    base_host = urlparse(base_url).netloc
    seen: set[str] = set()
    out: list[str] = []
    for raw in _HREF_RE.findall(html):
        href = raw.strip()
        if not href or href.lower().startswith(_SKIP_PREFIXES):
            continue
        absolute = urljoin(base_url, href).split("#", 1)[0]
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https") or parsed.netloc != base_host:
            continue
        if contains and contains not in absolute:
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        out.append(absolute)
        if len(out) >= limit:
            break
    return out


def extract_jsonld(html: str) -> list[dict]:
    """Parse all <script type=application/ld+json> blocks; flatten @graph.

    Malformed blocks are skipped, never fatal.
    """
    results: list[dict] = []
    for block in _JSONLD_RE.findall(html):
        try:
            data = json.loads(block.strip())
        except (json.JSONDecodeError, ValueError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            graph = item.get("@graph")
            if isinstance(graph, list):
                results.extend(node for node in graph if isinstance(node, dict))
            else:
                results.append(item)
    return results


class NavigateBridge(Protocol):
    """Injected browser that navigates the live session and captures a page."""

    async def navigate_capture(self, url: str) -> CaptureLike: ...


class DetailRecord(BaseModel):
    url: str
    title: str = ""
    markdown: str = ""
    jsonld: list[dict] = []
    blocked: bool = False
    vendor: str = ""
    error: str = ""


class CrawlFromHereResult(BaseModel):
    discovered: int = 0
    crawled: int = 0
    blocked: int = 0
    records: list[DetailRecord] = []


async def crawl_from_here(
    html: str,
    base_url: str,
    bridge: NavigateBridge,
    *,
    sleep: Callable[[float], Awaitable[None]],
    contains: str = "",
    limit: int = 5,
    delay: float = 1.0,
) -> CrawlFromHereResult:
    """Discover detail links on `html` and visit each in the cleared session."""
    links = extract_detail_links(html, base_url, contains=contains, limit=limit)
    records: list[DetailRecord] = []
    blocked = 0

    for index, link in enumerate(links):
        if index:  # polite pacing between detail pages
            await sleep(delay)
        try:
            cap = await bridge.navigate_capture(link)
        except Exception as exc:  # noqa: BLE001 — record and continue, never crash
            records.append(DetailRecord(url=link, error=f"nav failed: {exc}"))
            continue

        signal = detect_block(None, title=cap.title, html=cap.html, markdown=cap.text)
        if signal.blocked:
            blocked += 1
        records.append(
            DetailRecord(
                url=cap.url or link,
                title=cap.title,
                markdown=cap.text or "",
                jsonld=extract_jsonld(cap.html),
                blocked=signal.blocked,
                vendor=signal.vendor if signal.blocked else "",
            )
        )

    return CrawlFromHereResult(
        discovered=len(links), crawled=len(records), blocked=blocked, records=records
    )
